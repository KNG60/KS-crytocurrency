import random
import signal
import subprocess
import sys
import time
from pathlib import Path

import requests

PARENT_DIR = Path(__file__).parent.parent

HOST = "127.0.0.1"
START_PORT = 5000
MIN_NODES = 5
MAX_NODES = 10
MIN_SEEDS = 1
MAX_SEEDS = 5
MINER_PROBABILITY = 0.8
MINE_OPERATIONS_COUNT = 5


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

    result = subprocess.run(
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
        self.node_ports = []
        self.miner_ports = []

    def cleanup(self, signum=None, frame=None):
        print("\n\nShutting down all nodes...")
        for proc in self.processes:
            proc.terminate()

        print("All nodes stopped.")
        sys.exit(0)

    def start_node(self, port, seed_peers=None, is_miner=False):
        node_index = port - START_PORT
        wallet_label = create_node_account(node_index)

        cmd = [
            sys.executable,
            "run_node.py",
            "--host", HOST,
            "--port", str(port),
            "--role", "miner" if is_miner else "normal",
            "--wallet-label", wallet_label
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
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
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
        print(f"CREATING RANDOM P2P NETWORK")
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

        print("\nAccess network visualization:")
        for port in self.node_ports[:3]:
            print(f"  http://localhost:{port}/static/network.html")
        if len(self.node_ports) > 3:
            print(f"  ... and {len(self.node_ports) - 3} more")

        print("=" * 70 + "\n")

    def perform_mine_operations(self):
        if not self.miner_ports:
            print("\nNo miners available for mining operations.")
            return

        print("\n" + "=" * 70)
        print("STARTING MINING OPERATIONS")
        print("=" * 70)
        print(f"Will perform {MINE_OPERATIONS_COUNT} mining operations")
        print(f"Available miners: {len(self.miner_ports)}")
        print("=" * 70 + "\n")

        for i in range(MINE_OPERATIONS_COUNT):
            miner_port = random.choice(self.miner_ports)

            print(f"[{i + 1}/{MINE_OPERATIONS_COUNT}] Sending mine request to port {miner_port}...", end=" ")

            try:
                response = requests.post(
                    f"http://{HOST}:{miner_port}/mine",
                    timeout=10
                )

                if response.status_code == 200:
                    print(f"✓ SUCCESS - Block mined: {response.json()}")
                else:
                    print(f"✗ FAILED - Status: {response.status_code}")

            except requests.exceptions.Timeout:
                print("✗ FAILED - Timeout")
            except requests.exceptions.ConnectionError:
                print("✗ FAILED - Connection error (miner might be down)")

            time.sleep(1)

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
    print("PREPARING ENVIRONMENT")
    print("=" * 70)
    kill_node_processes()
    clean_databases()
    print("=" * 70 + "\n")

    time.sleep(1)

    manager = NetworkManager()

    signal.signal(signal.SIGINT, manager.cleanup)
    signal.signal(signal.SIGTERM, manager.cleanup)

    try:
        manager.create_random_network()

        print("Waiting for network to stabilize...")
        time.sleep(3)

        manager.perform_mine_operations()

        print("\nPress Ctrl+C to stop all nodes")

        manager.wait_forever()
    except Exception as e:
        print(f"\nError: {e}")
        manager.cleanup()
        sys.exit(1)


if __name__ == '__main__':
    main()
