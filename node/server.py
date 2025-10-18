import logging
from threading import Thread

from flask import Flask, request, jsonify

from node.network import NetworkClient
from node.storage import PeerStorage

logger = logging.getLogger(__name__)


class NodeServer:
    def __init__(self, host: str, port: int, db_path: str, seed_peers: list):
        self.host = host
        self.port = port
        self.storage = PeerStorage(db_path)
        self.network = NetworkClient()
        self.seed_peers = seed_peers
        self.app = Flask(__name__)
        self._setup_routes()

    def is_self_peer(self, peer_host: str, peer_port: int) -> bool:
        return peer_host == self.host and peer_port == self.port

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

            if not self.network.ping_peer(peer_host, peer_port):
                return jsonify({"error": "Peer is not reachable"}), 503

            logger.info(f"Registering new peer {peer_host}:{peer_port}")

            self.storage.add_peer(peer_host, peer_port)

            return jsonify({"host": peer_host, "port": peer_port}), 201

    def bootstrap(self):
        logger.info(f"Bootstrapping node with {len(self.seed_peers)} seed peers")
        for seed in self.seed_peers:
            seed_host, seed_port = seed['host'], seed['port']
            logger.info(f"Connecting to seed peer {seed_host}:{seed_port}")

            if self.network.register_with_peer(seed_host, seed_port, self.host, self.port):
                self.storage.add_peer(seed_host, seed_port)

                peers = self.network.fetch_peers_from_peer(seed_host, seed_port)
                if peers:
                    for peer in peers:
                        host, port = peer['host'], peer['port']
                        if (not self.is_self_peer(host, port)
                                and self.network.register_with_peer(host, port, self.host, self.port)):
                            self.storage.add_peer(host, port)

    def run(self):
        if self.seed_peers:
            Thread(target=self.bootstrap, daemon=True).start()

        logger.info(f"Starting node on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port)
