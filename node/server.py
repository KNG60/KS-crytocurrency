import logging
import os
import random
from threading import Thread
from typing import Set, Tuple

from flask import Flask, Response, jsonify, request

from node.blockchain import Block, Blockchain
from node.graph import NetworkGraphManager
from node.network import NetworkClient
from node.storage import ChainStorage, PeerStorage
from node.transactions import SignedTransaction

logger = logging.getLogger(__name__)

MAX_PEERS = 5
MAX_BOOTSTRAP_PEERS = 3
DIFFICULTY = 5


class NodeServer:
    def __init__(self, host: str, port: int, seed_peers: list, *, role: str = "normal", public_key: str):
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
        self.graph_manager = NetworkGraphManager(host, port, self.storage, self.network)
        self.app = Flask(__name__, static_folder='../static', static_url_path='/static')
        self._setup_routes()
        self.role = role
        self.blockchain = Blockchain(DIFFICULTY)
        self.chain_storage = ChainStorage(chain_db_path)
        self.pending_transactions: list[SignedTransaction] = []
        self._init_chain()

    def _init_chain(self):
        local_chain = self.chain_storage.load_chain()
        local_len = len(local_chain)

        best_chain = None
        if self.seed_peers:
            for seed in self.seed_peers:
                host, port = seed.get('host'), int(seed.get('port'))
                chain = self.network.fetch_chain_from_peer(host, port)
                if chain and (best_chain is None or len(chain) > len(best_chain)):
                    best_chain = chain

        adopted = False
        if best_chain and len(best_chain) > local_len:
            if self.blockchain.validate_chain(best_chain):
                self.chain_storage.replace_chain(best_chain)
                logger.info(f"Adopted longer chain from seed: {len(best_chain)} blocks (local had {local_len})")
                adopted = True

        if not adopted and local_len == 0:
            genesis = self.blockchain.create_genesis()
            self.chain_storage.save_block(genesis.to_dict())
            logger.info(f"Genesis created: h=0 hash={genesis.hash[:16]}...")

    def _try_adopt_longer_chain(self, min_target_len: int | None = None) -> tuple[bool, int]:
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
            chain = self.network.fetch_chain_from_peer(host, port)
            if not chain:
                continue
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
        logger.info(f"Runtime adoption: replaced local chain ({local_len}) with longer chain ({target_len})")
        return (True, target_len)

    def is_self_peer(self, peer_host: str, peer_port: int) -> bool:
        return peer_host == self.host and peer_port == self.port

    def add_transaction(self, signed_tx: SignedTransaction) -> bool:
        for tx in self.pending_transactions:
            if tx.signature == signed_tx.signature:
                return False
        self.pending_transactions.append(signed_tx)
        logger.info(f"Added transaction to mempool: {signed_tx.transaction.txid[:16]}...")
        return True

    def broadcast_transaction(self, transaction: dict):
        peers = self.storage.get_all_peers()
        self.network.broadcast_transaction(peers, transaction)

    def _remove_inactive_peers(self):
        peer_list = self.storage.get_all_peers()
        for peer in peer_list:
            peer_host, peer_port = peer['host'], peer['port']
            if not self.network.ping_peer(peer_host, peer_port):
                logger.info(f"Removing inactive peer {peer_host}:{peer_port}")
                self.storage.remove_peer(peer_host, peer_port)
                self.graph_manager.notify_graph_change()

    def _setup_routes(self):
        @self.app.route('/ping', methods=['GET'])
        def ping():
            return jsonify({"status": "ok"}), 200

        @self.app.route('/peers', methods=['GET'])
        def get_peers():
            peers = self.storage.get_all_peers()
            return jsonify(peers), 200

        @self.app.route('/network-graph', methods=['GET'])
        def network_graph():
            return jsonify(self.graph_manager.get_network_graph_data()), 200

        @self.app.route('/network-stream', methods=['GET'])
        def network_stream():
            return Response(self.graph_manager.create_sse_event_stream(), mimetype='text/event-stream')

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
            self.graph_manager.notify_graph_change()

            return jsonify({"host": peer_host, "port": peer_port}), 201

        @self.app.route('/blocks', methods=['GET'])
        def get_blocks():
            chain = self.chain_storage.load_chain()
            return jsonify(chain), 200

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

            if not self.blockchain.validate_block(incoming, prev):
                local_height = prev.height if prev else -1
                should_try_adopt = incoming.height >= local_height + 1
                if should_try_adopt:
                    adopted, new_len = self._try_adopt_longer_chain(min_target_len=incoming.height + 1)
                    if adopted:
                        return jsonify({"status": "reorganized", "height": new_len - 1}), 201
                return jsonify({"error": "invalid block"}), 400

            self.chain_storage.save_block(incoming.to_dict())

            peers = self.storage.get_all_peers()
            self.network.broadcast_block(peers, incoming.to_dict())
            return jsonify({"status": "accepted", "height": incoming.height}), 201

        @self.app.route('/mine', methods=['POST'])
        def mine():
            if self.role != "miner":
                return jsonify({"error": "node is not a miner"}), 403

            last_d = self.chain_storage.get_last_block()
            prev = Block.from_dict(last_d) if last_d else self.blockchain.create_genesis()

            new_block = self.blockchain.mine_next_block(prev, self.public_key, txs=[])
            self.chain_storage.save_block(new_block.to_dict())

            peers = self.storage.get_all_peers()
            self.network.broadcast_block(peers, new_block.to_dict())

            return jsonify(new_block.to_dict()), 200

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

            if self.add_transaction(signed_tx):
                self.broadcast_transaction(data)
                return jsonify({"status": "accepted", "txid": signed_tx.transaction.txid}), 201
            return jsonify({"status": "already exists", "txid": signed_tx.transaction.txid}), 200

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
                self.graph_manager.notify_graph_change()

                if successes >= MAX_BOOTSTRAP_PEERS:
                    break

        logger.info(f"Bootstrap completed: registered with {successes} peers")

    def run(self):
        if self.seed_peers:
            Thread(target=self.bootstrap, daemon=True).start()

        logger.info(f"Starting node on {self.host}:{self.port} role={self.role}")
        self.app.run(host=self.host, port=self.port)
