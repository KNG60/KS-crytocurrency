import logging
from typing import Dict, List, Optional

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

    def submit_block_to_peer(self, peer_host: str, peer_port: int, block: Dict) -> bool:
        url = f"http://{peer_host}:{peer_port}/blocks"
        try:
            r = requests.post(url, json=block, timeout=self.timeout)
            if r.status_code in (200, 201):
                logger.info(f"Submitted block h={block.get('height')} to {peer_host}:{peer_port}")
                return True
            logger.warning(f"Peer {peer_host}:{peer_port} rejected block: {r.status_code} {r.text}")
            return False
        except requests.ConnectionError:
            logger.warning(f"Peer {peer_host}:{peer_port} is unreachable for block submit")
            return False

    def broadcast_block(self, peers: List[Dict], block: Dict):
        ok = 0
        for p in peers:
            if self.submit_block_to_peer(p['host'], int(p['port']), block):
                ok += 1
        logger.info(f"Broadcasted block h={block.get('height')} to {ok}/{len(peers)} peers")
