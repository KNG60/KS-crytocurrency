import random
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import List

import requests

PARENT_DIR = Path(__file__).parent.parent

HOST = "127.0.0.1"
START_PORT_A = 5200
START_PORT_B = 5300
MIN_NODES = 3
MAX_NODES = 4
MIN_SEEDS = 1
MAX_SEEDS = 2
MINER_PROBABILITY = 0.5
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


def create_node_account(label: str) -> str:
    result = subprocess.run(
        [sys.executable, "run_wallet.py", "add", label],
        cwd=str(PARENT_DIR),
        input="demo\n",
        text=True,
        capture_output=True
    )
    return label


class DualNetworkManager:
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.net_a_ports: List[int] = []
        self.net_b_ports: List[int] = []
        self.net_a_miners: List[int] = []
        self.net_b_miners: List[int] = []
        self.centralized_manager_process = None

    def cleanup(self, signum=None, frame=None):
        print("\n\nShutting down all nodes...")
        for proc in self.processes:
            try:
                proc.terminate()
            except Exception:
                pass

        if self.centralized_manager_process:
            print("Shutting down centralized graph manager...")
            try:
                self.centralized_manager_process.terminate()
            except Exception:
                pass

        print("All nodes stopped.")
        sys.exit(0)

    def start_centralized_manager(self):
        print("Starting network graph manager on port", CENTRALIZED_MANAGER_PORT)
        print(f"  http://{HOST}:{CENTRALIZED_MANAGER_PORT}/static/network.html")

        cmd = [
            sys.executable,
            "-c",
            (
                "from demo.graph_manager import CentralizedGraphManager; "
                "import logging; "
                "logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'); "
                f"manager = CentralizedGraphManager('{HOST}', {CENTRALIZED_MANAGER_PORT}); "
                "manager.run()"
            )
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

    def start_node(self, port: int, seeds: List[int], is_miner: bool):
        node_index = port  # use port in label to avoid collisions
        wallet_label = f"node_{node_index}"
        create_node_account(wallet_label)

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

        if seeds:
            seeds_str = ",".join([f"{HOST}:{p}" for p in seeds])
            cmd.extend(["--seeds", seeds_str])

        role_label = "MINER" if is_miner else "normal"
        print(f"Starting node on port {port} (role: {role_label}, wallet: {wallet_label})", end="")
        if seeds:
            print(f" with seeds: {seeds}")
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
        time.sleep(0.1)
        return proc

    def build_network(self, start_port: int, label: str):
        size = random.randint(MIN_NODES, MAX_NODES)
        ports = [start_port + i for i in range(size)]
        miners: List[int] = []

        print("\n" + "=" * 70)
        print(f"CREATING NETWORK {label} ({size} nodes)")
        print("=" * 70)

        # First node
        first_port = ports[0]
        is_first_miner = random.random() < MINER_PROBABILITY
        self.start_node(first_port, seeds=[], is_miner=is_first_miner)
        if is_first_miner:
            miners.append(first_port)

        # Others
        for port in ports[1:]:
            is_miner = random.random() < MINER_PROBABILITY
            num_seeds = random.randint(MIN_SEEDS, min(MAX_SEEDS, len(ports)))
            seed_peers = random.sample(ports[:ports.index(port)], k=min(num_seeds, ports.index(port)))
            self.start_node(port, seeds=seed_peers, is_miner=is_miner)
            if is_miner:
                miners.append(port)

        print(f"Network {label} ports: {ports}")
        print(f"Miners in {label}: {miners}")
        return ports, miners

    def ensure_miners_running(self, miner_ports: List[int]):
        for p in miner_ports:
            try:
                requests.post(f"http://{HOST}:{p}/miner/start", timeout=2)
            except Exception:
                pass

    def connect_networks(self, a_port: int, b_port: int):
        print(f"Connecting networks via {a_port} ↔ {b_port}...")
        # Bidirectional peer add
        try:
            ra = requests.post(
                f"http://{HOST}:{a_port}/peers",
                json={"host": HOST, "port": b_port},
                timeout=3
            )
            print(" A -> B:", ra.status_code, ra.text)
        except Exception as e:
            print(" A -> B failed:", e)

        try:
            rb = requests.post(
                f"http://{HOST}:{b_port}/peers",
                json={"host": HOST, "port": a_port},
                timeout=3
            )
            print(" B -> A:", rb.status_code, rb.text)
        except Exception as e:
            print(" B -> A failed:", e)

        # Optional: notify manager (nodes also notify on peer add)
        try:
            requests.post(f"http://{HOST}:{CENTRALIZED_MANAGER_PORT}/notify", timeout=2)
        except Exception:
            pass

    def wait_forever(self):
        try:
            while True:
                time.sleep(1)
                for proc in self.processes:
                    if proc.poll() is not None:
                        print("Warning: a node process has stopped!")
        except KeyboardInterrupt:
            self.cleanup()


def main():
    print("\n" + "=" * 70)
    print("PREPARING ENVIRONMENT (dual networks)")
    print("=" * 70)
    kill_node_processes()
    clean_databases()
    print("=" * 70 + "\n")

    time.sleep(1)

    mgr = DualNetworkManager()

    signal.signal(signal.SIGINT, mgr.cleanup)
    signal.signal(signal.SIGTERM, mgr.cleanup)

    try:
        mgr.start_centralized_manager()
        time.sleep(2)

        ports_a, miners_a = mgr.build_network(START_PORT_A, label="A")
        ports_b, miners_b = mgr.build_network(START_PORT_B, label="B")

        print("Waiting for networks to stabilize...")
        time.sleep(3)

        mgr.ensure_miners_running(miners_a)
        mgr.ensure_miners_running(miners_b)

        print("\n" + "=" * 70)
        print("NETWORKS READY")
        print("=" * 70)
        print(f"A: ports={ports_a} miners={miners_a}")
        print(f"B: ports={ports_b} miners={miners_b}")
        print("\nOpen UI:")
        print(f"  http://{HOST}:{CENTRALIZED_MANAGER_PORT}/static/network.html")

        print("\nPress Enter to connect networks using")
        try:
            user = input(f"Default pair: {ports_a[0]} {ports_b[0]} > ").strip()
        except EOFError:
            user = ""
        if user:
            try:
                a_p, b_p = [int(x) for x in user.split()]  # expects two ints
            except Exception:
                print("Invalid input; using default pair")
                a_p, b_p = ports_a[0], ports_b[0]
        else:
            a_p, b_p = ports_a[0], ports_b[0]

        mgr.connect_networks(a_p, b_p)

        print("\nPress Ctrl+C to stop all nodes")
        mgr.wait_forever()
    except Exception as e:
        print(f"\nError: {e}")
        mgr.cleanup()
        sys.exit(1)


if __name__ == '__main__':
    main()
