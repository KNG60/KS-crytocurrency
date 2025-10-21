import logging
from typing import List, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class NetworkClient:
    def __init__(self, timeout: int = 5):
        self.timeout = timeout

    def register_as_inbound_peer(self, peer_host: str, peer_port: int, own_host: str, own_port: int) -> bool:
        url = f"http://{peer_host}:{peer_port}/peers"
        payload = {"host": own_host, "port": own_port}

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            if response.status_code == 201:
                logger.info(f"Successfully registered as inbound peer for {peer_host}:{peer_port}")
                return True
            else:
                logger.warning(
                    f"Failed to register as inbound peer for {peer_host}:{peer_port}: {response.status_code}")
                return False
        except requests.ConnectionError:
            logger.warning(f"Peer {peer_host}:{peer_port} is unreachable")
            return False

    def fetch_peers_from_peer(self, peer_host: str, peer_port: int) -> Optional[List[Dict]]:
        try:
            url = f"http://{peer_host}:{peer_port}/peers"
            response = requests.get(url, timeout=self.timeout)
            if response.status_code == 200:
                peers = response.json()
                logger.info(f"Fetched {len(peers)} peers from {peer_host}:{peer_port}")
                return peers
            else:
                logger.warning(f"Failed to fetch peers from {peer_host}:{peer_port}: {response.status_code}")
                return None
        except requests.ConnectionError:
            logger.warning(f"Peer {peer_host}:{peer_port} is unreachable")
            return None

    def ping_peer(self, peer_host: str, peer_port: int) -> bool:
        url = f"http://{peer_host}:{peer_port}/ping"
        try:
            response = requests.get(url, timeout=self.timeout)
            return response.status_code == 200
        except requests.ConnectionError:
            logger.warning(f"Peer {peer_host}:{peer_port} is unreachable")
            return False
