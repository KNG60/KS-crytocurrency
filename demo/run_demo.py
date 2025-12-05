import subprocess
import sys
from pathlib import Path

PARENT_DIR = Path(__file__).parent.parent

ALICE_NODE_PORT = 5001
BOB_NODE_PORT = 5002

node_processes = []


def start_node(wallet_label: str, port: int, role: str = "normal"):
    print(f"Starting {role} node for {wallet_label} on port {port}...")
    proc = subprocess.Popen(
        [sys.executable, "run_node.py",
         "--host", "127.0.0.1",
         "--port", str(port),
         "--role", role,
         "--wallet-label", wallet_label],
        cwd=str(PARENT_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    node_processes.append(proc)
    return proc


def stop_all_nodes():
    print("\nStopping all nodes...")
    for proc in node_processes:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    node_processes.clear()


def run_cmd(cmd, password=None):
    proc = subprocess.Popen(
        [sys.executable, "run_wallet.py"] + cmd.split(),
        cwd=str(PARENT_DIR),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = proc.communicate(input=f"{password}\n" if password else None)
    print(stdout)
    if stderr and proc.returncode != 0:
        print(f"Error: {stderr}")
    return proc.returncode


def demo_wallet():
    print("\n" + "=" * 70)
    print("PART 1: WALLET OPERATIONS")
    print("=" * 70)

    wallet_db_dir = PARENT_DIR / "wallet" / "db"
    if wallet_db_dir.exists():
        for db_file in wallet_db_dir.glob("*.db"):
            db_file.unlink()
        print("Cleaned up previous databases\n")

    print("1. Creating accounts (alice, bob, charlie)...")
    for name in ["alice", "bob", "charlie"]:
        run_cmd(f"add {name}", password="demo123")

    print("\n2. Listing accounts...")
    run_cmd("list")

    print("\n3. Showing alice's details...")
    run_cmd("show alice")

    print("\n4. Showing alice's private key...")
    run_cmd("show-priv alice", password="demo123")

    print("\n5. Deleting charlie's account...")
    run_cmd("delete charlie")

    print("\n6. Listing accounts after deletion...")
    run_cmd("list")


def demo_transactions():
    print("\n" + "=" * 70)
    print("PART 2: TRANSACTION OPERATIONS & MINING")
    print("=" * 70)

    print("\n1. Initial account states...")
    run_cmd("show alice")
    run_cmd("show bob")

    print("\n2. Starting blockchain nodes...")
    print("   - Alice's node (miner) on port 5001")
    start_node("alice", ALICE_NODE_PORT, role="miner")
    print("   - Bob's node (miner) on port 5002")
    start_node("bob", BOB_NODE_PORT, role="miner")

    print("\n3. Mining block on alice's node (port 5001)...")
    run_cmd(f"mine --node http://127.0.0.1:{ALICE_NODE_PORT}")

    print("\n4. Mining block on bob's node (port 5002)...")
    run_cmd(f"mine --node http://127.0.0.1:{BOB_NODE_PORT}")

    print("\n5. Creating transaction: alice -> bob (25.0 coins)...")
    run_cmd(f"create-tx alice bob 25.0 --node http://127.0.0.1:{ALICE_NODE_PORT}", password="demo123")

    print("\n6. Creating transaction: bob -> alice (10.0 coins)...")
    run_cmd(f"create-tx bob alice 10.0 --node http://127.0.0.1:{BOB_NODE_PORT}", password="demo123")

    print("\n7. Mining another block to include pending transactions...")
    print("   Mining on alice's node...")
    run_cmd(f"mine --node http://127.0.0.1:{ALICE_NODE_PORT}")

    print("\n8. Note: Balances are tracked on the blockchain")
    print("   Use GET /blocks to query blockchain state from nodes")
    run_cmd("show alice")
    run_cmd("show bob")


def main():
    print("\n" + "#" * 70)
    print("# FULL DEMO")
    print("#" * 70)

    try:
        demo_wallet()

        demo_transactions()

        print("\n" + "=" * 70)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 70)

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    finally:
        stop_all_nodes()
        sys.exit(0)


if __name__ == '__main__':
    main()
