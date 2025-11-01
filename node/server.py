import logging
import random
from threading import Thread
from typing import Set, Tuple

from flask import Flask, Response, jsonify, request

from node.blockchain import Block, Blockchain
from node.graph import NetworkGraphManager
from node.network import NetworkClient
from node.storage import ChainStorage, PeerStorage

logger = logging.getLogger(__name__)

MAX_PEERS = 5
MAX_BOOTSTRAP_PEERS = 3


class NodeServer:
    def __init__(self, host: str, port: int, db_path: str, seed_peers: list, *, chain_db_path: str | None = None, role: str = "full", difficulty: int = 4):
        self.host = host
        self.port = port
        self.storage = PeerStorage(db_path)
        self.network = NetworkClient()
        self.seed_peers = seed_peers
        self.graph_manager = NetworkGraphManager(host, port, self.storage, self.network)
        self.app = Flask(__name__, static_folder='../static', static_url_path='/static')
        self._setup_routes()
        self.role = role
        self.blockchain = Blockchain(difficulty)
        self.chain_storage = ChainStorage(chain_db_path or db_path)
        self._init_chain()
        

    def _init_chain(self):
        last = self.chain_storage.get_last_block()
        if last is None:
            genesis = self.blockchain.create_genesis()
            self.chain_storage.save_block(genesis.to_dict())
            logger.info(f"Genesis created: h=0 hash={genesis.hash[:16]}...")

    def is_self_peer(self, peer_host: str, peer_port: int) -> bool:
        return peer_host == self.host and peer_port == self.port

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

            miner_id = f"{self.host}:{self.port}"
            new_block = self.blockchain.mine_next_block(prev, miner_id, txs=[])
            self.chain_storage.save_block(new_block.to_dict())

            peers = self.storage.get_all_peers()
            self.network.broadcast_block(peers, new_block.to_dict())

            return jsonify({"status": "mined", "block": new_block.to_dict()}), 200

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
