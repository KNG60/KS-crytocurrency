import logging
import random
from threading import Thread
from typing import Set, Tuple

from flask import Flask, request, jsonify

from node.network import NetworkClient
from node.storage import PeerStorage

logger = logging.getLogger(__name__)

MAX_INBOUND_PEERS = 5
MAX_OUTBOUND_PEERS = 3


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

    def _remove_inactive_inbound_peers(self):
        inbound_list = self.storage.get_inbound_peers()
        for peer in inbound_list:
            inbound_peer_host, inbound_peer_port = peer['host'], peer['port']
            if not self.network.ping_peer(inbound_peer_host, inbound_peer_port):
                logger.info(f"Removing inactive inbound peer {inbound_peer_host}:{inbound_peer_port}")
                self.storage.remove_inbound_peer(inbound_peer_host, inbound_peer_port)

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

            inbound_count = self.storage.count_inbound_peers()
            if inbound_count >= MAX_INBOUND_PEERS:
                logger.info("Inbound limit reached, checking for inactive inbound peers to free slots")
                self._remove_inactive_inbound_peers()
                inbound_count = self.storage.count_inbound_peers()
                if inbound_count >= MAX_INBOUND_PEERS:
                    return jsonify({"error": "Inbound peer limit reached"}), 429

            if not self.network.ping_peer(peer_host, peer_port):
                return jsonify({"error": "Peer is not reachable"}), 503

            logger.info(f"Accepting inbound registration from {peer_host}:{peer_port}")
            self.storage.add_inbound_peer(peer_host, peer_port)

            return jsonify({"host": peer_host, "port": peer_port}), 201

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
        logger.info(f"Discovered {len(candidate_list)} unique candidate peers for outbound registration")

        successes = 0
        for host, port in candidate_list:
            if self.network.register_as_inbound_peer(host, port, self.host, self.port):
                self.storage.add_outbound_peer(host, port)
                successes += 1
                logger.info(f"Registered outbound with {host}:{port} ({successes}/{MAX_OUTBOUND_PEERS})")
                if successes >= MAX_OUTBOUND_PEERS:
                    break

    def run(self):
        if self.seed_peers:
            Thread(target=self.bootstrap, daemon=True).start()

        logger.info(f"Starting node on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port)
