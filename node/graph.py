import json
import logging
import queue
from typing import Dict, List, Set

from node.network import NetworkClient
from node.storage import PeerStorage

logger = logging.getLogger(__name__)


def _build_nodes_list(visited: Set[str], current_node_id: str, network_data: Dict) -> List[Dict]:
    nodes = []
    all_nodes = sorted(visited)

    for node_id in all_nodes:
        is_current = (node_id == current_node_id)
        is_reachable = network_data.get(node_id, {}).get("reachable", False)

        nodes.append({
            "id": node_id,
            "label": node_id.split(':')[1],
            "color": "#4CAF50" if is_current else ("#888" if not is_reachable else None)
        })

    return nodes


def _build_edges_list(network_data: Dict) -> List[Dict]:
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


class NetworkGraphManager:
    def __init__(self, host: str, port: int, storage: PeerStorage, network: NetworkClient):
        self.host = host
        self.port = port
        self.storage = storage
        self.network = network
        self._sse_clients = []

    def get_network_graph_data(self) -> Dict:
        current_node_id = f"{self.host}:{self.port}"
        network_data = {}
        to_visit = [current_node_id]
        visited = set()

        while to_visit:
            node_id = to_visit.pop(0)

            if node_id in visited:
                continue

            visited.add(node_id)

            if node_id == current_node_id:
                peers = self.storage.get_all_peers()
                network_data[node_id] = {
                    "peers": peers,
                    "reachable": True
                }
            else:
                host, port = node_id.rsplit(':', 1)
                port = int(port)

                try:
                    peers = self.network.fetch_peers_from_peer(host, port)
                    if peers is not None:
                        network_data[node_id] = {
                            "peers": peers,
                            "reachable": True
                        }
                    else:
                        network_data[node_id] = {"peers": [], "reachable": False}
                except Exception as e:
                    logger.debug(f"Could not fetch peers from {node_id}: {e}")
                    network_data[node_id] = {"peers": [], "reachable": False}

            for peer in network_data[node_id]["peers"]:
                peer_id = f"{peer['host']}:{peer['port']}"
                if peer_id not in visited:
                    to_visit.append(peer_id)

        nodes = _build_nodes_list(visited, current_node_id, network_data)
        edges = _build_edges_list(network_data)

        return {"nodes": nodes, "edges": edges}

    def notify_graph_change(self):
        data = self.get_network_graph_data()
        message = f"data: {json.dumps(data)}\n\n"

        self._sse_clients = [client for client in self._sse_clients if client(message)]

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

        self._sse_clients.append(send_update)

        try:
            while True:
                message = q.get()
                yield message
        except GeneratorExit:
            self._sse_clients.remove(send_update)
