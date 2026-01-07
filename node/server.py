import logging
import os
import random
import re
import time
from threading import Event, Thread
from typing import Dict, List, Optional, Set, Tuple

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

from node.blockchain import (
    MINING_MIN,
    Block,
    Blockchain,
    calculate_balance_with_mempool,
)
from node.network import NetworkClient
from node.storage import ChainStorage, PeerStorage
from node.transactions import SignedTransaction

logger = logging.getLogger(__name__)

MAX_PEERS = 5
MAX_BOOTSTRAP_PEERS = 3
DIFFICULTY = 5


class NodeServer:
    def __init__(self, host: str, port: int, seed_peers: list, *, role: str = "normal", public_key: str,
                 centralized_manager_url: Optional[str] = None):
        self.host = host
        self.port = port
        self.public_key = public_key

        server_dir = os.path.dirname(os.path.abspath(__file__))
        db_dir = os.path.join(server_dir, 'db')
        os.makedirs(db_dir, exist_ok=True)

        peers_db_path = os.path.join(db_dir, f'peers_{port}.db')
        chain_db_path = os.path.join(db_dir, f'chain_{port}.db')

        self.storage = PeerStorage(peers_db_path)
        self.network = NetworkClient()
        self.seed_peers = seed_peers
        self.role = role
        self.blockchain = Blockchain(DIFFICULTY)
        self.chain_storage = ChainStorage(chain_db_path)
        self.pending_transactions: list[SignedTransaction] = []
        self.centralized_manager_url = centralized_manager_url
        self.app = Flask(__name__, static_folder='../static', static_url_path='/static')
        CORS(self.app, resources={
            "/*": {"origins": [re.compile(r"^http://127.0.0.1:\d+$")]}
        })

        # Orphan and fork handling (in-memory)
        # key: prev_hash -> list of blocks whose parent is prev_hash
        self.orphans_by_prev: Dict[str, List[Block]] = {}
        # quick known set to avoid reprocessing duplicates
        self.known_hashes: Set[str] = set()

        self._setup_routes()
        self._init_chain()

        if self.centralized_manager_url:
            Thread(target=self._register_with_centralized_manager, daemon=True).start()

        self.mining_enabled: bool = False
        self.mining_thread: Optional[Thread] = None
        self.mining_stop_event: Event = Event()

    def _mining_worker(self):
        logger.info("Mining thread started")
        while self.mining_enabled:
            try:
                self.mining_stop_event.clear()
                last_d = self.chain_storage.get_last_block()
                prev = Block.from_dict(last_d) if last_d else self.blockchain.create_genesis()

                txs_snapshot = list(self.pending_transactions)

                new_block = self.blockchain.mine_next_block(
                    prev,
                    self.public_key,
                    txs=txs_snapshot,
                    stop_event=self.mining_stop_event
                )

                if not self.mining_enabled:
                    break
                if new_block is None:
                    continue

                self.chain_storage.save_block(new_block.to_dict())
                self.remove_transactions_from_mempool(new_block)

                peers = self.storage.get_all_peers()
                self.network.broadcast_block(peers, new_block.to_dict())

                self._notify_centralized_manager()
                logger.info(f"Mined new block h={new_block.height} hash={new_block.hash[:16]}...")
            except Exception as e:
                logger.error(f"Mining thread error: {type(e).__name__}: {e}")
                time.sleep(0.5)
        logger.info("Mining thread stopped")

    def _interrupt_mining(self):
        if hasattr(self, 'mining_stop_event') and self.mining_stop_event is not None:
            self.mining_stop_event.set()

    def start_mining(self):
        if self.role != "miner":
            logger.info("Node role is not 'miner'; skipping start_mining")
            return False
        if self.mining_enabled and self.mining_thread and self.mining_thread.is_alive():
            return True
        self.mining_enabled = True
        self.mining_thread = Thread(target=self._mining_worker, daemon=True)
        self.mining_thread.start()
        return True

    def stop_mining(self):
        if not self.mining_enabled:
            return True
        self.mining_enabled = False
        self._interrupt_mining()
        try:
            if self.mining_thread:
                self.mining_thread.join(timeout=2)
        except Exception:
            pass
        return True

    def _register_with_centralized_manager(self):
        time.sleep(2)
        max_retries = 10
        retry_delay = 0.5
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.centralized_manager_url}/register-node",
                    json={"host": self.host, "port": self.port},
                    timeout=10
                )
                if response.status_code == 201:
                    logger.info(f"Registered with graph manager at {self.centralized_manager_url}")
                    return
                else:
                    logger.warning(f"Failed to register: HTTP {response.status_code}")
            except requests.exceptions.ConnectionError as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.warning(f"Could not register with manager after {max_retries} attempts: connection error")
            except requests.exceptions.Timeout as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.warning(f"Could not register with manager after {max_retries} attempts: timeout")
            except Exception as e:
                logger.error(f"Unexpected error during registration: {type(e).__name__}: {e}")
                return

    def _notify_centralized_manager(self):
        if self.centralized_manager_url:
            try:
                requests.post(
                    f"{self.centralized_manager_url}/notify",
                    timeout=1
                )
            except Exception as e:
                logger.debug(f"Could not notify centralized manager: {e}")

    def _init_chain(self):
        local_chain = self.chain_storage.load_chain()
        local_len = len(local_chain)

        best_chain = None
        best_peer_host = None
        best_peer_port = None

        if self.seed_peers:
            for seed in self.seed_peers:
                host, port = seed.get('host'), int(seed.get('port'))
                chain_dicts = self.network.fetch_chain_from_peer(host, port)
                if chain_dicts:
                    chain = [Block.from_dict(b) for b in chain_dicts]
                    if best_chain is None or len(chain) > len(best_chain):
                        best_chain = chain
                        best_peer_host = host
                        best_peer_port = port

        adopted = False
        if best_chain and len(best_chain) > local_len:
            if self.blockchain.validate_chain(best_chain):
                self.chain_storage.replace_chain(best_chain)
                for block in best_chain:
                    self.remove_transactions_from_mempool(block)
                logger.info(f"Adopted longer chain from seed: {len(best_chain)} blocks (local had {local_len})")
                adopted = True

                if best_peer_host and best_peer_port:
                    tx_dicts = self.network.fetch_pending_transactions_from_peer(best_peer_host, best_peer_port)
                    if tx_dicts:
                        for tx_dict in tx_dicts:
                            try:
                                signed_tx = SignedTransaction.from_dict(tx_dict)
                                self.add_transaction(signed_tx)
                            except Exception as e:
                                logger.warning(f"Failed to add transaction from peer mempool: {e}")
                        logger.info(f"Synchronized {len(self.pending_transactions)} transactions from peer mempool")

        if not adopted and local_len == 0:
            genesis = self.blockchain.create_genesis()
            self.chain_storage.save_block(genesis.to_dict())
            logger.info(f"Genesis created: h=0 hash={genesis.hash[:16]}...")

        # Index known main chain hashes for orphan linkage
        main_chain = self.chain_storage.load_chain()
        self.known_hashes = {b.hash for b in main_chain}

    def _try_adopt_longer_chain(self, min_target_len: int) -> tuple[bool, int]:
        local_len = len(self.chain_storage.load_chain())
        peers_set: set[tuple[str, int]] = set()
        for s in self.seed_peers or []:
            try:
                peers_set.add((s.get('host'), int(s.get('port'))))
            except Exception:
                pass
        for p in self.storage.get_all_peers():
            try:
                host = p.get('host')
                port_val = p.get('port')
                if host and port_val is not None:
                    peers_set.add((host, int(port_val)))
            except Exception:
                pass

        best_chain = None
        for host, port in peers_set:
            chain_dicts = self.network.fetch_chain_from_peer(host, port)
            if not chain_dicts:
                continue
            chain = [Block.from_dict(b) for b in chain_dicts]
            if best_chain is None or len(chain) > len(best_chain):
                best_chain = chain

        if not best_chain:
            return (False, local_len)

        target_len = len(best_chain)
        if min_target_len is not None and target_len < min_target_len:
            return (False, local_len)
        if target_len <= local_len:
            return (False, local_len)

        if not self.blockchain.validate_chain(best_chain):
            return (False, local_len)

        self.chain_storage.replace_chain(best_chain)

        for block in best_chain:
            self.remove_transactions_from_mempool(block)

        logger.info(f"Runtime adoption: replaced local chain ({local_len}) with longer chain ({target_len})")
        return (True, target_len)

    def is_self_peer(self, peer_host: str, peer_port: int) -> bool:
        return peer_host == self.host and peer_port == self.port

    def add_transaction(self, signed_tx: SignedTransaction) -> None:
        for tx in self.pending_transactions:
            if tx.signature == signed_tx.signature:
                raise ValueError("Transaction already in mempool")

        transaction = signed_tx.transaction

        if transaction.sender is None:
            raise ValueError("Coinbase transaction rejected - coinbase can only be created during mining")

        chain = self.chain_storage.load_chain()

        sender_public_key = transaction.sender
        sender_balance = calculate_balance_with_mempool(chain, sender_public_key, self.pending_transactions)
        if sender_balance < transaction.amount:
            raise ValueError(f"Insufficient balance: {sender_balance} < {transaction.amount}")

        self.pending_transactions.append(signed_tx)
        logger.info(
            f"Added transaction to mempool: {signed_tx.transaction.txid[:16]}... (mempool size: {len(self.pending_transactions)})")

    def broadcast_transaction(self, transaction: dict):
        peers = self.storage.get_all_peers()
        self.network.broadcast_transaction(peers, transaction)

    def remove_transactions_from_mempool(self, block: Block):
        block_txids = {tx.transaction.txid for tx in block.txs}

        original_count = len(self.pending_transactions)
        self.pending_transactions = [
            tx for tx in self.pending_transactions
            if tx.transaction.txid not in block_txids
        ]
        removed_count = original_count - len(self.pending_transactions)

        if removed_count > 0:
            logger.info(f"Removed {removed_count} transactions from mempool (found in new block)")
            self._notify_centralized_manager()

        return removed_count

    def _remove_inactive_peers(self):
        peer_list = self.storage.get_all_peers()
        for peer in peer_list:
            peer_host, peer_port = peer['host'], peer['port']
            if not self.network.ping_peer(peer_host, peer_port):
                logger.info(f"Removing inactive peer {peer_host}:{peer_port}")
                self.storage.remove_peer(peer_host, peer_port)
                self._notify_centralized_manager()

    def _setup_routes(self):
        @self.app.route('/ping', methods=['GET'])
        def ping():
            return jsonify({"status": "ok"}), 200

        @self.app.route('/peers', methods=['GET'])
        def get_peers():
            peers = self.storage.get_all_peers()
            return jsonify(peers), 200

        @self.app.route('/peers', methods=['POST'])
        def add_peer():
            data = request.get_json()
            if not data or 'host' not in data or 'port' not in data:
                return jsonify({"error": "Missing host or port"}), 400

            peer_host = data['host']
            peer_port = int(data['port'])

            if self.is_self_peer(peer_host, peer_port):
                return jsonify({"error": "Cannot register self as peer"}), 400

            peer_count = self.storage.count_peers()
            if peer_count >= MAX_PEERS:
                logger.info(f"Peer limit reached ({peer_count}/{MAX_PEERS}), checking for inactive peers")
                self._remove_inactive_peers()
                peer_count = self.storage.count_peers()
                if peer_count >= MAX_PEERS:
                    return jsonify({"error": "Peer limit reached"}), 429

            if not self.network.ping_peer(peer_host, peer_port):
                return jsonify({"error": "Peer is not reachable"}), 503

            logger.info(f"Accepting peer registration from {peer_host}:{peer_port}")
            self.storage.add_peer(peer_host, peer_port)
            self._notify_centralized_manager()

            return jsonify({"host": peer_host, "port": peer_port}), 201

        @self.app.route('/blocks', methods=['GET'])
        def get_blocks():
            chain = self.chain_storage.load_chain()
            return jsonify([block.to_dict() for block in chain]), 200

        @self.app.route('/blocks', methods=['POST'])
        def receive_block():
            data = request.get_json()
            if not data:
                return jsonify({"error": "missing block body"}), 400
            try:
                incoming = Block.from_dict(data)
            except Exception as e:
                return jsonify({"error": f"malformed block: {e}"}), 400

            last = self.chain_storage.get_last_block()
            prev = Block.from_dict(last) if last else None

            chain = self.chain_storage.load_chain()
            chain_with_incoming = chain + [incoming]

            if not self.blockchain.validate_chain(chain_with_incoming):
                # If it doesn't attach to tip, treat as possible orphan/fork candidate
                local_height = prev.height if prev else -1

                # Fast path: if this block references a known parent in our main chain, stash as orphan
                # and trigger reorg attempt if its height exceeds our tip
                if incoming.prev_hash in self.known_hashes:
                    # Basic per-block validation against its stated parent
                    parent_block = next((b for b in chain if b.hash == incoming.prev_hash), None)
                    if parent_block and self.blockchain.validate_block(incoming, parent_block):
                        self._store_orphan(incoming)
                        # If the orphan's height is beyond our tip, try adopt a longer chain from peers
                        if incoming.height > local_height:
                            adopted, new_len = self._try_adopt_longer_chain(min_target_len=incoming.height + 1)
                            if adopted:
                                self._interrupt_mining()
                                self.remove_transactions_from_mempool(incoming)
                                self._notify_centralized_manager()
                                return jsonify({"status": "reorganized", "height": new_len - 1}), 201
                        # Accepted as orphan
                        return jsonify({"status": "orphan-buffered", "height": incoming.height}), 202
                else:
                    # Parent unknown: cache under its prev_hash to link later
                    self._store_orphan(incoming)
                    return jsonify({"status": "orphan-buffered", "height": incoming.height}), 202

                # If we got here, try network-driven adoption for clearly longer chains
                should_try_adopt = incoming.height >= local_height + 1
                if should_try_adopt:
                    adopted, new_len = self._try_adopt_longer_chain(min_target_len=incoming.height + 1)
                    if adopted:
                        self._interrupt_mining()
                        self.remove_transactions_from_mempool(incoming)
                        self._notify_centralized_manager()
                        return jsonify({"status": "reorganized", "height": new_len - 1}), 201
                return jsonify({"error": "invalid block"}), 400

            self.chain_storage.save_block(incoming.to_dict())

            self.remove_transactions_from_mempool(incoming)

            # Mark as known and attempt to flush any orphans that now extend the tip
            self.known_hashes.add(incoming.hash)
            self._flush_orphans_extending_tip()

            peers = self.storage.get_all_peers()
            self.network.broadcast_block(peers, incoming.to_dict())

            self._notify_centralized_manager()

            # Interrupt mining so the miner restarts on the new tip
            self._interrupt_mining()

            return jsonify({"status": "accepted", "height": incoming.height}), 201

        @self.app.route('/mine', methods=['POST'])
        def mine():
            if self.role != "miner":
                return jsonify({"error": "node is not a miner"}), 403

            last_d = self.chain_storage.get_last_block()
            prev = Block.from_dict(last_d) if last_d else self.blockchain.create_genesis()

            new_block = self.blockchain.mine_next_block(prev, self.public_key, txs=self.pending_transactions)
            if new_block is None:
                return jsonify({"error": "mining interrupted"}), 503
            self.chain_storage.save_block(new_block.to_dict())

            self.pending_transactions.clear()

            # Update known set and flush any now-attachable orphans
            self.known_hashes.add(new_block.hash)
            self._flush_orphans_extending_tip()

            peers = self.storage.get_all_peers()
            self.network.broadcast_block(peers, new_block.to_dict())

            self._notify_centralized_manager()

            return jsonify(new_block.to_dict()), 200

        @self.app.route('/balance/<public_key>', methods=['GET'])
        def get_balance(public_key):
            chain = self.chain_storage.load_chain()
            balance = calculate_balance_with_mempool(chain, public_key, self.pending_transactions)
            return str(balance), 200

        @self.app.route('/info', methods=['GET'])
        def get_info():
            chain = self.chain_storage.load_chain()
            balance = calculate_balance_with_mempool(chain, self.public_key, self.pending_transactions)
            # Flatten orphan blocks for UI diagnostics
            orphan_blocks: List[Dict] = []
            for lst in self.orphans_by_prev.values():
                for b in lst:
                    orphan_blocks.append(b.to_dict())
            # Sort by height then hash for stable view
            orphan_blocks.sort(key=lambda d: (int(d.get("height", -1)), str(d.get("hash", ""))))
            return jsonify({
                "public_key": self.public_key,
                "balance": balance,
                "role": self.role,
                "chain": [block.to_dict() for block in chain],
                "pending_transactions": [tx.to_dict() for tx in self.pending_transactions],
                "forks": orphan_blocks
            }), 200

        @self.app.route('/transactions', methods=['GET'])
        def get_transactions():
            return jsonify([tx.to_dict() for tx in self.pending_transactions]), 200

        @self.app.route('/transactions', methods=['POST'])
        def receive_transaction():
            data = request.get_json()
            if not data:
                return jsonify({"error": "missing transaction body"}), 400

            try:
                signed_tx = SignedTransaction.from_dict(data)
            except Exception as e:
                return jsonify({"error": f"invalid transaction: {e}"}), 400

            try:
                prev_count = len(self.pending_transactions)
                self.add_transaction(signed_tx)
                new_count = len(self.pending_transactions)
                # Restart mining only when mempool size crosses the MINING_MIN threshold
                if prev_count < MINING_MIN and new_count > MINING_MIN:
                    self._interrupt_mining()
                self.broadcast_transaction(data)
                self._notify_centralized_manager()
                return jsonify({"status": "accepted", "txid": signed_tx.transaction.txid}), 201
            except Exception as e:
                return jsonify({"status": "rejected", "txid": signed_tx.transaction.txid, "error": str(e)}), 400

        @self.app.route('/miner/start', methods=['POST'])
        def miner_start():
            if self.role != "miner":
                return jsonify({"error": "node is not a miner"}), 403
            started = self.start_mining()
            return jsonify({"status": "started" if started else "noop"}), 200

        @self.app.route('/miner/stop', methods=['POST'])
        def miner_stop():
            stopped = self.stop_mining()
            return jsonify({"status": "stopped" if stopped else "noop"}), 200

        @self.app.route('/miner/status', methods=['GET'])
        def miner_status():
            is_running = self.mining_enabled and self.mining_thread and self.mining_thread.is_alive()
            return jsonify({"running": bool(is_running), "role": self.role}), 200

    def bootstrap(self):
        logger.info(f"Bootstrapping node with {len(self.seed_peers)} seed peers")
        candidates: Set[Tuple[str, int]] = set()

        for seed in self.seed_peers:
            seed_host, seed_port = seed['host'], seed['port']
            if not self.is_self_peer(seed_host, seed_port):
                candidates.add((seed_host, int(seed_port)))

            logger.info(f"Querying seed peer {seed_host}:{seed_port} for peers")
            peers = self.network.fetch_peers_from_peer(seed_host, seed_port)
            if peers is not None:
                for peer in peers:
                    host, port = peer['host'], int(peer['port'])
                    if not self.is_self_peer(host, port):
                        candidates.add((host, port))

        candidate_list = list(candidates)
        random.shuffle(candidate_list)
        logger.info(f"Discovered {len(candidate_list)} unique candidate peers for registration")

        successes = 0
        for host, port in candidate_list:
            if self.network.register_as_inbound_peer(host, port, self.host, self.port):
                self.storage.add_peer(host, port)
                successes += 1
                logger.info(f"Registered with peer {host}:{port} ({successes}/{MAX_BOOTSTRAP_PEERS})")
                self._notify_centralized_manager()

                if successes >= MAX_BOOTSTRAP_PEERS:
                    break

        logger.info(f"Bootstrap completed: registered with {successes} peers")

    def run(self):
        if self.seed_peers:
            Thread(target=self.bootstrap, daemon=True).start()

        logger.info(f"Starting node on {self.host}:{self.port} role={self.role}")

        if self.role == "miner":
            self.start_mining()
        self.app.run(host=self.host, port=self.port)

    # -------------------- Fork / Orphan helpers --------------------
    def _store_orphan(self, block: Block) -> None:
        if block.hash in self.known_hashes:
            return
        self.orphans_by_prev.setdefault(block.prev_hash, []).append(block)
        self.known_hashes.add(block.hash)
        logger.info(f"Buffered orphan block h={block.height} hash={block.hash[:16]}... (prev={block.prev_hash[:16]}...)")

    def _flush_orphans_extending_tip(self) -> None:
        """Attach any orphans that directly extend the current tip, iteratively.
        If multiple orphans compete at the same parent, keep them buffered as forks.
        """
        while True:
            last_d = self.chain_storage.get_last_block()
            if not last_d:
                break
            tip_hash = str(last_d["hash"])
            candidates = self.orphans_by_prev.get(tip_hash) or []
            if not candidates:
                break
            # Choose one deterministically (e.g., smallest hash) to extend; others remain as forks
            candidates.sort(key=lambda b: b.hash)
            next_block = candidates.pop(0)
            if not candidates:
                # Remove empty list to stop loop when no more children
                self.orphans_by_prev.pop(tip_hash, None)
            else:
                # Keep remaining candidates under same parent
                self.orphans_by_prev[tip_hash] = candidates

            # Try to append and broadcast
            chain = self.chain_storage.load_chain()
            chain_with = chain + [next_block]
            if self.blockchain.validate_chain(chain_with):
                self.chain_storage.save_block(next_block.to_dict())
                self.remove_transactions_from_mempool(next_block)
                self.known_hashes.add(next_block.hash)
                peers = self.storage.get_all_peers()
                self.network.broadcast_block(peers, next_block.to_dict())
                self._notify_centralized_manager()
                logger.info(f"Attached orphan h={next_block.height} to tip; chain extended")
                # Continue loop in case there are further descendants
                continue
            else:
                # If appended chain invalid, keep it buffered (do not discard) and stop
                self.orphans_by_prev.setdefault(tip_hash, []).append(next_block)
                break
