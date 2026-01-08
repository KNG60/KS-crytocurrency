import random
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict

# Ensure project root is on sys.path to import 'node' package
PARENT_DIR = Path(__file__).parent.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

import requests

from node.blockchain import Blockchain, Block, SignedTransaction

HOST = "127.0.0.1"
START_PORT = 5000
MIN_NODES = 7
MAX_NODES = 10
MIN_SEEDS = 1
MAX_SEEDS = 5
MINER_PROBABILITY = 0.4
CENTRALIZED_MANAGER_PORT = 8080

# Attack params
ORPHAN_CHAIN_LENGTH = 3          # how many blocks to mine on stale parent
ORPHAN_BASE_OFFSET = 2           # mine starting at tip - ORPHAN_BASE_OFFSET
ATTACK_TARGET_COUNT = 3          # how many victim nodes to target
DIFFICULTY = 5                   # must match node/server.py DIFFICULTY


def kill_node_processes():
    print("Killing any existing node processes...")
    subprocess.run(["pkill", "-9", "-f", "run_node.py"], check=False)


def clean_databases():
    db_dir = PARENT_DIR / "node" / "db"
    if db_dir.exists():
        print(f"Cleaning node database directory: {db_dir}")
        for db_file in db_dir.glob("*.db"):
            db_file.unlink()
        print("  Node database directory cleaned successfully")

    wallet_db_dir = PARENT_DIR / "wallet" / "db"
    if wallet_db_dir.exists():
        print(f"Cleaning wallet database directory: {wallet_db_dir}")
        for db_file in wallet_db_dir.glob("*.db"):
            db_file.unlink()
        print("  Wallet database directory cleaned successfully")


def create_node_account(node_index: int) -> str:
    label = f"node_{node_index}"

    subprocess.run(
        [sys.executable, "run_wallet.py", "add", label],
        cwd=str(PARENT_DIR),
        input="demo\n",
        text=True,
        capture_output=True
    )

    return label


class NetworkManager:
    def __init__(self):
        self.processes = []
        self.node_ports: List[int] = []
        self.miner_ports: List[int] = []
        self.centralized_manager_process = None

    def cleanup(self, signum=None, frame=None):
        print("\n\nShutting down all nodes...")
        for proc in self.processes:
            proc.terminate()

        if self.centralized_manager_process:
            print("Shutting down centralized graph manager...")
            self.centralized_manager_process.terminate()

        print("All nodes stopped.")
        sys.exit(0)

    def start_centralized_manager(self):
        print("Starting network graph manager on port", CENTRALIZED_MANAGER_PORT)
        print(f"  http://{HOST}:{CENTRALIZED_MANAGER_PORT}/static/network.html")

        cmd = [
            sys.executable,
            "-c",
            f"from demo.graph_manager import CentralizedGraphManager; "
            f"import logging; "
            f"logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'); "
            f"manager = CentralizedGraphManager('{HOST}', {CENTRALIZED_MANAGER_PORT}); "
            f"manager.run()"
        ]

        proc = subprocess.Popen(
            cmd,
            cwd=str(PARENT_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True
        )

        self.centralized_manager_process = proc
        time.sleep(1)
        return proc

    def start_node(self, port, seed_peers=None, is_miner=False):
        node_index = port - START_PORT
        wallet_label = create_node_account(node_index)

        centralized_manager_url = f"http://{HOST}:{CENTRALIZED_MANAGER_PORT}"

        cmd = [
            sys.executable,
            "run_node.py",
            "--host", HOST,
            "--port", str(port),
            "--role", "miner" if is_miner else "normal",
            "--wallet-label", wallet_label,
            "--centralized-manager", centralized_manager_url
        ]

        if seed_peers:
            seeds_str = ",".join([f"{HOST}:{p}" for p in seed_peers])
            cmd.extend(["--seeds", seeds_str])

        role_label = "MINER" if is_miner else "normal"
        print(f"Starting node on port {port} (role: {role_label}, wallet: {wallet_label})", end="")
        if seed_peers:
            print(f" with seeds: {seed_peers}")
        else:
            print(" (bootstrap node)")

        proc = subprocess.Popen(
            cmd,
            cwd=str(PARENT_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True
        )

        self.processes.append(proc)
        self.node_ports.append(port)

        if is_miner:
            self.miner_ports.append(port)

        time.sleep(0.1)

        return proc

    def create_random_network(self):
        num_nodes = random.randint(MIN_NODES, MAX_NODES)

        print("\n" + "=" * 70)
        print(f"CREATING RANDOM P2P NETWORK (fork attack demo)")
        print("=" * 70)
        print(f"Number of nodes: {num_nodes}")
        print(f"Port range: {START_PORT} - {START_PORT + num_nodes - 1}")
        print(f"Miner probability: {MINER_PROBABILITY * 100}%")
        print("=" * 70 + "\n")

        first_port = START_PORT
        is_first_miner = random.random() < MINER_PROBABILITY
        self.start_node(first_port, is_miner=is_first_miner)

        for i in range(1, num_nodes):
            port = START_PORT + i
            is_miner = random.random() < MINER_PROBABILITY

            num_seeds = random.randint(MIN_SEEDS, min(MAX_SEEDS, len(self.node_ports)))
            seed_peers = random.sample(self.node_ports, num_seeds)

            self.start_node(port, seed_peers, is_miner=is_miner)

        print("\n" + "=" * 70)
        print("NETWORK STARTED SUCCESSFULLY")
        print("=" * 70)
        print(f"\nAll {num_nodes} nodes are running.")
        print(f"Miners: {len(self.miner_ports)} nodes")
        print(f"Normal nodes: {num_nodes - len(self.miner_ports)} nodes")

        if self.miner_ports:
            print(f"\nMiner ports: {self.miner_ports}")

        print("=" * 70 + "\n")

    def ensure_miners_running(self):
        for p in self.miner_ports:
            try:
                requests.post(f"http://{HOST}:{p}/miner/start", timeout=2)
            except Exception:
                pass

    def fetch_chain(self, port: int) -> List[Dict]:
        try:
            r = requests.get(f"http://{HOST}:{port}/blocks", timeout=3)
            if r.status_code == 200:
                return r.json()
        except Exception:
            return []
        return []

    def broadcast_block(self, block: Dict, ports: List[int]):
        for port in ports:
            try:
                r = requests.post(f"http://{HOST}:{port}/blocks", json=block, timeout=3)
                status = r.status_code
                print(f"  → Sent block h={block.get('height')} to {port}: {status}")
            except Exception as e:
                print(f"  → Failed to send block to {port}: {e}")

    def mine_orphan_chain(self, base_block_dict: Dict, length: int, miner_id: str) -> List[Dict]:
        bc = Blockchain(DIFFICULTY)
        chain: List[Dict] = []
        prev = Block.from_dict(base_block_dict)
        txs: List[SignedTransaction] = []
        for i in range(length):
            blk = bc.mine_next_block(prev, miner_id, txs)
            if not blk:
                break
            chain.append(blk.to_dict())
            prev = blk
        return chain

    def attack_force_forks(self):
        print("\n" + "=" * 70)
        print("ATTACK PHASE: Forcing forks by injecting orphan chain")
        print("=" * 70)

        # Choose victims
        victims = random.sample(self.node_ports, min(ATTACK_TARGET_COUNT, len(self.node_ports)))
        print(f"Victim ports: {victims}")

        # Use the first victim as reference to pick a stale parent
        ref_port = victims[0]
        ref_chain = self.fetch_chain(ref_port)
        if not ref_chain or len(ref_chain) <= ORPHAN_BASE_OFFSET:
            print("Insufficient chain height for attack; skipping")
            return
        tip_h = len(ref_chain) - 1
        base_h = max(0, tip_h - ORPHAN_BASE_OFFSET)
        base_block = ref_chain[base_h]
        print(f"Using base parent height={base_block['height']} hash={base_block['hash'][:16]}...")

        # Mine a short orphan chain on top of the stale parent
        orphan_chain = self.mine_orphan_chain(base_block, ORPHAN_CHAIN_LENGTH, miner_id="malicious")
        print(f"Mined orphan chain length={len(orphan_chain)} starting at h={base_block['height']}")

        # Broadcast each orphan block to all victims
        for b in orphan_chain:
            self.broadcast_block(b, victims)
            time.sleep(0.2)

        print("Attack complete. Check UI 'Fork Chain' sections for buffered orphans.")

    def wait_forever(self):
        try:
            while True:
                time.sleep(1)

                for i, proc in enumerate(self.processes):
                    if proc.poll() is not None:
                        print(f"\nWarning: Node on port {self.node_ports[i]} has stopped!")

        except KeyboardInterrupt:
            self.cleanup()


def main():
    print("\n" + "=" * 70)
    print("PREPARING ENVIRONMENT (fork attack)")
    print("=" * 70)
    kill_node_processes()
    clean_databases()
    print("=" * 70 + "\n")

    time.sleep(1)

    manager = NetworkManager()

    signal.signal(signal.SIGINT, manager.cleanup)
    signal.signal(signal.SIGTERM, manager.cleanup)

    try:
        manager.start_centralized_manager()

        time.sleep(2)

        manager.create_random_network()

        print("Waiting for network to stabilize...")
        time.sleep(3)

        manager.ensure_miners_running()
        time.sleep(1)

        # Attack phase
        manager.attack_force_forks()

        print("\nPress Ctrl+C to stop all nodes")

        manager.wait_forever()
    except Exception as e:
        print(f"\nError: {e}")
        manager.cleanup()
        sys.exit(1)


if __name__ == '__main__':
    main()
