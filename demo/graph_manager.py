import json
import logging
import queue
import threading
from typing import Dict, List, Set

import requests
from flask import Flask, Response, jsonify
from flask_cors import CORS

logger = logging.getLogger(__name__)


class CentralizedGraphManager:
    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        self.host = host
        self.port = port
        self.known_nodes: Set[str] = set()
        self._sse_clients = set()
        self.app = Flask(__name__, static_folder='../static', static_url_path='/static')
        CORS(self.app)
        self._setup_routes()
        self._lock = threading.Lock()

    def add_node(self, node_host: str, node_port: int):
        node_id = f"{node_host}:{node_port}"
        with self._lock:
            if node_id not in self.known_nodes:
                self.known_nodes.add(node_id)
                logger.info(f"Registered node: {node_id}, total nodes: {len(self.known_nodes)}")
                threading.Thread(target=self.notify_graph_change, daemon=True).start()

    def get_network_graph_data(self) -> Dict:
        network_data = {}
        visited = set()

        with self._lock:
            to_visit = list(self.known_nodes)

        while to_visit:
            node_id = to_visit.pop(0)

            if node_id in visited:
                continue

            visited.add(node_id)

            host, port = node_id.rsplit(':', 1)
            port = int(port)

            try:
                peers_response = requests.get(f"http://{host}:{port}/peers", timeout=2)
                info_response = requests.get(f"http://{host}:{port}/info", timeout=2)

                if peers_response.status_code == 200:
                    peers = peers_response.json()
                    info = info_response.json() if info_response.status_code == 200 else {}

                    network_data[node_id] = {
                        "peers": peers,
                        "reachable": True,
                        "info": info
                    }
                else:
                    network_data[node_id] = {"peers": [], "reachable": False, "info": {}}
            except Exception as e:
                logger.debug(f"Could not fetch data from {node_id}: {e}")
                network_data[node_id] = {"peers": [], "reachable": False, "info": {}}

            for peer in network_data[node_id]["peers"]:
                peer_id = f"{peer['host']}:{peer['port']}"
                if peer_id not in visited:
                    to_visit.append(peer_id)

        nodes = self._build_nodes_list(visited, network_data)
        edges = self._build_edges_list(network_data)

        return {"nodes": nodes, "edges": edges}

    def notify_graph_change(self):
        data = self.get_network_graph_data()
        message = f"data: {json.dumps(data)}\n\n"

        active_clients = len(self._sse_clients)
        self._sse_clients = {client for client in self._sse_clients if client(message)}
        logger.info(f"Graph update sent to {active_clients} SSE clients")

    def create_sse_event_stream(self):
        data = self.get_network_graph_data()
        yield f"data: {json.dumps(data)}\n\n"

        q = queue.Queue()

        def send_update(message):
            try:
                q.put(message, block=False)
                return True
            except:
                return False

        self._sse_clients.add(send_update)

        try:
            while True:
                message = q.get()
                yield message
        except GeneratorExit:
            self._sse_clients.discard(send_update)

    def _build_nodes_list(self, visited: Set[str], network_data: Dict) -> List[Dict]:
        nodes = []
        all_nodes = sorted(visited)

        for node_id in all_nodes:
            is_reachable = network_data.get(node_id, {}).get("reachable", False)
            node_info = network_data.get(node_id, {}).get("info", {})

            balance = node_info.get("balance", 0)
            label = f"{node_id.split(':')[1]}\n{balance}"

            node_data = {
                "id": node_id,
                "label": label,
                "color": "#888" if not is_reachable else None,
                "info": node_info
            }

            nodes.append(node_data)

        return nodes

    def _build_edges_list(self, network_data: Dict) -> List[Dict]:
        all_edges = set()

        for node_id, data in network_data.items():
            if not data.get("reachable"):
                continue

            for peer in data["peers"]:
                peer_id = f"{peer['host']}:{peer['port']}"
                edge = tuple(sorted([node_id, peer_id]))
                all_edges.add(edge)

        edges = [{"from": edge[0], "to": edge[1]} for edge in all_edges]
        return edges

    def _setup_routes(self):
        @self.app.route('/ping', methods=['GET'])
        def ping():
            return jsonify({"status": "ok"}), 200

        @self.app.route('/register-node', methods=['POST'])
        def register_node():
            from flask import request
            data = request.get_json()
            if not data or 'host' not in data or 'port' not in data:
                return jsonify({"error": "Missing host or port"}), 400

            self.add_node(data['host'], int(data['port']))
            return jsonify({"status": "registered"}), 201

        @self.app.route('/notify', methods=['POST'])
        def notify():
            threading.Thread(target=self.notify_graph_change, daemon=True).start()
            return jsonify({"status": "notified"}), 200

        @self.app.route('/network-graph', methods=['GET'])
        def network_graph():
            return jsonify(self.get_network_graph_data()), 200

        @self.app.route('/network-stream', methods=['GET'])
        def network_stream():
            return Response(self.create_sse_event_stream(), mimetype='text/event-stream')

    def run(self):
        logger.info(f"Starting graph manager on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, threaded=True, use_reloader=False)
