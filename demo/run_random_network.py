import random
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

PARENT_DIR = Path(__file__).parent.parent

HOST = "127.0.0.1"
START_PORT = 5000
MIN_NODES = 10
MAX_NODES = 20
MIN_SEEDS = 1
MAX_SEEDS = 5


def kill_node_processes():
    print("Killing any existing node processes...")
    subprocess.run(["pkill", "-9", "-f", "run_node.py"], check=False)


def clean_databases():
    db_dir = PARENT_DIR / "db"
    if db_dir.exists():
        print(f"Cleaning database directory: {db_dir}")
        shutil.rmtree(db_dir)
        db_dir.mkdir()
        print("  Database directory cleaned successfully")


class NetworkManager:
    def __init__(self):
        self.processes = []
        self.node_ports = []

    def cleanup(self, signum=None, frame=None):
        print("\n\nShutting down all nodes...")
        for proc in self.processes:
            proc.terminate()

        print("All nodes stopped.")
        sys.exit(0)

    def start_node(self, port, seed_peers=None):
        cmd = [
            sys.executable,
            "run_node.py",
            "--host", HOST,
            "--port", str(port)
        ]

        if seed_peers:
            seeds_str = ",".join([f"{HOST}:{p}" for p in seed_peers])
            cmd.extend(["--seeds", seeds_str])

        print(f"Starting node on port {port}", end="")
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

        time.sleep(0.5)

        return proc

    def create_random_network(self):
        num_nodes = random.randint(MIN_NODES, MAX_NODES)

        print("\n" + "=" * 70)
        print(f"CREATING RANDOM P2P NETWORK")
        print("=" * 70)
        print(f"Number of nodes: {num_nodes}")
        print(f"Port range: {START_PORT} - {START_PORT + num_nodes - 1}")
        print("=" * 70 + "\n")

        first_port = START_PORT
        self.start_node(first_port)

        for i in range(1, num_nodes):
            port = START_PORT + i

            num_seeds = random.randint(MIN_SEEDS, min(MAX_SEEDS, len(self.node_ports)))
            seed_peers = random.sample(self.node_ports, num_seeds)

            self.start_node(port, seed_peers)

        print("\n" + "=" * 70)
        print("NETWORK STARTED SUCCESSFULLY")
        print("=" * 70)
        print(f"\nAll {num_nodes} nodes are running.")
        print("\nAccess network visualization:")
        for port in self.node_ports[:3]:
            print(f"  http://localhost:{port}/static/network.html")
        if len(self.node_ports) > 3:
            print(f"  ... and {len(self.node_ports) - 3} more")

        print("\nPress Ctrl+C to stop all nodes")
        print("=" * 70 + "\n")

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
        manager.wait_forever()
    except Exception as e:
        print(f"\nError: {e}")
        manager.cleanup()
        sys.exit(1)


if __name__ == '__main__':
    main()
