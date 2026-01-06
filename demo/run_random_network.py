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
MIN_NODES = 3
MAX_NODES = 3
MIN_SEEDS = 1
MAX_SEEDS = 5
MINER_PROBABILITY = 0.8
MINE_OPERATIONS_COUNT = 3
CENTRALIZED_MANAGER_PORT = 8080


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
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
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

        print("=" * 70 + "\n")

    def perform_mine_operations(self):
        if not self.miner_ports:
            print("\nNo miners available for mining operations.")
            return

        print("\n" + "=" * 70)
        print("STARTING MINING OPERATIONS (async)")
        print("=" * 70)
        print(f"Will perform {MINE_OPERATIONS_COUNT} mining checks")
        print(f"Available miners: {len(self.miner_ports)}")
        print("=" * 70 + "\n")

        # Ensure all miners are running
        for p in self.miner_ports:
            try:
                requests.post(f"http://{HOST}:{p}/miner/start", timeout=2)
            except Exception:
                pass

        def get_height(port: int) -> int:
            try:
                r = requests.get(f"http://{HOST}:{port}/blocks", timeout=3)
                if r.status_code == 200:
                    return len(r.json())
            except Exception:
                return -1
            return -1

        for i in range(MINE_OPERATIONS_COUNT):
            miner_port = random.choice(self.miner_ports)
            print(f"[{i + 1}/{MINE_OPERATIONS_COUNT}] Trigger/start mining on port {miner_port}...", end=" ")

            # Start miner (idempotent) and wait for chain height to increase
            try:
                requests.post(f"http://{HOST}:{miner_port}/miner/start", timeout=3)
            except Exception:
                print("✗ FAILED - cannot contact miner")
                continue

            h0 = get_height(miner_port)
            if h0 < 0:
                print("✗ FAILED - cannot read height")
                continue

            deadline = time.time() + 20 
            mined = False
            while time.time() < deadline:
                time.sleep(0.5)
                h1 = get_height(miner_port)
                if h1 > h0:
                    mined = True
                    break

            if mined:
                print(f"✓ SUCCESS - New height {h1} (was {h0})")
            else:
                print("⋯ NO BLOCK WITHIN TIME BUDGET")

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
        manager.start_centralized_manager()

        time.sleep(2)

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
