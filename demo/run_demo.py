import subprocess
import sys
import time
from pathlib import Path

import requests

from node.transactions import Transaction, SignedTransaction
from wallet.storage import get_account_details

PARENT_DIR = Path(__file__).parent.parent

ALICE_NODE_PORT = 5001
BOB_NODE_PORT = 5002

node_processes = []


def start_node(wallet_label: str, port: int, role: str = "normal", seeds: str = ""):
    print(f"Starting {role} node for {wallet_label} on port {port}...")
    cmd = [sys.executable, "run_node.py",
           "--host", "127.0.0.1",
           "--port", str(port),
           "--role", role,
           "--wallet-label", wallet_label]

    if seeds:
        cmd.extend(["--seeds", seeds])

    proc = subprocess.Popen(
        cmd,
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


def demo_wallet():
    print("\n" + "=" * 70)
    print("PART 1: WALLET OPERATIONS")
    print("=" * 70)

    print("1. Creating accounts (alice, bob, charlie)...")
    for name in ["alice", "bob", "charlie"]:
        run_cmd(f"add {name}", password="demo123")

    print("\n2. Listing accounts...")
    run_cmd("list")

    print("\n3. Showing alice's private key...")
    run_cmd("show-priv alice", password="demo123")

    print("\n4. Deleting charlie's account...")
    run_cmd("delete charlie")

    print("\n5. Listing accounts after deletion...")
    run_cmd("list")


def demo_transactions():
    print("\n" + "=" * 70)
    print("PART 2: TRANSACTION OPERATIONS & MINING")
    print("=" * 70)

    print("\n1. Starting blockchain nodes...")
    print("   - Alice's node (miner) on port 5001")
    start_node("alice", ALICE_NODE_PORT, role="miner")
    print("   - Bob's node (miner) on port 5002 (with Alice as seed peer)")
    start_node("bob", BOB_NODE_PORT, role="miner", seeds=f"127.0.0.1:{ALICE_NODE_PORT}")

    print("   Waiting for nodes to initialize and connect...")
    time.sleep(2)

    print("\n2. Checking initial account states (should be 0)...")
    run_cmd(f"show alice --node http://127.0.0.1:{ALICE_NODE_PORT}")
    run_cmd(f"show bob --node http://127.0.0.1:{BOB_NODE_PORT}")

    print("\n3. Mining block on alice's node (port 5001)...")
    run_cmd(f"mine --node http://127.0.0.1:{ALICE_NODE_PORT}")

    print("\n4. Mining block on bob's node (port 5002)...")
    run_cmd(f"mine --node http://127.0.0.1:{BOB_NODE_PORT}")

    print("\n5. Checking balances after mining rewards...")
    run_cmd(f"show alice --node http://127.0.0.1:{ALICE_NODE_PORT}")
    run_cmd(f"show bob --node http://127.0.0.1:{BOB_NODE_PORT}")

    print("\n6. Creating transaction: alice -> bob (25.0 coins)...")
    run_cmd(f"create-tx alice bob 25.0 --node http://127.0.0.1:{ALICE_NODE_PORT}", password="demo123")

    print("\n7. Creating transaction: bob -> alice (10.0 coins)...")
    run_cmd(f"create-tx bob alice 10.0 --node http://127.0.0.1:{BOB_NODE_PORT}", password="demo123")

    print("   Waiting for transaction propagation...")
    time.sleep(1)

    print("\n8. Mining another block to include pending transactions...")
    print("   Mining on alice's node...")
    run_cmd(f"mine --node http://127.0.0.1:{ALICE_NODE_PORT}")

    print("\n9. Checking final balances from blockchain...")
    run_cmd(f"show alice --node http://127.0.0.1:{ALICE_NODE_PORT}")
    run_cmd(f"show bob --node http://127.0.0.1:{BOB_NODE_PORT}")


def demo_invalid_transactions():
    print("\n" + "=" * 70)
    print("PART 3: INVALID TRANSACTIONS")
    print("=" * 70)

    print("\n1. Trying to create transaction with insufficient balance...")
    print("   Alice tries to send 1000 coins (more than she has)...")
    run_cmd(f"create-tx alice bob 1000.0 --node http://127.0.0.1:{ALICE_NODE_PORT}", password="demo123")

    alice_account = get_account_details("alice")
    bob_account = get_account_details("bob")

    alice_pubkey = alice_account['pubkey_hex']
    bob_pubkey = bob_account['pubkey_hex']

    print("\n2. Trying to bypass validation by sending negative amount via HTTP...")

    fake_tx_negative = Transaction(
        sender=alice_pubkey,
        recipient=bob_pubkey,
        amount=50.0,
        timestamp=int(time.time()),
    )
    signed_fake_negative = SignedTransaction(fake_tx_negative, "deadbeef" * 16)
    fake_negative_dict = signed_fake_negative.to_dict()
    fake_negative_dict["amount"] = -50.0

    response = requests.post(
        f"http://127.0.0.1:{ALICE_NODE_PORT}/transactions",
        json=fake_negative_dict,
        timeout=5
    )
    if response.ok:
        print("   ✗ PROBLEM: Transaction with negative amount was accepted!")
        print(f"   Response: {response.text}")
    else:
        print(f"   ✓ Transaction rejected by node - CORRECT")
        print(f"   Error: {response.status_code} - {response.text}")

    print("\n3. Sending transaction with invalid txid via HTTP...")

    fake_tx_invalid = Transaction(
        sender=alice_pubkey,
        recipient=bob_pubkey,
        amount=100.0,
        timestamp=int(time.time()),
    )
    signed_fake_invalid = SignedTransaction(fake_tx_invalid, "deadbeef" * 16)
    fake_tx_dict = signed_fake_invalid.to_dict()
    fake_tx_dict["txid"] = "1" * 64

    response = requests.post(
        f"http://127.0.0.1:{ALICE_NODE_PORT}/transactions",
        json=fake_tx_dict,
        timeout=5
    )
    if response.ok:
        print("   ⚠ PROBLEM: Transaction was accepted into mempool")
        print(f"   Response: {response.text}")
    else:
        print(f"   ✓ Transaction rejected by node - CORRECT")
        print(f"   Error: {response.status_code} - {response.text}")

    print("\n4. Sending transaction with fake signature via HTTP...")

    fake_tx_valid_txid = Transaction(
        sender=alice_pubkey,
        recipient=bob_pubkey,
        amount=50.0,
        timestamp=int(time.time()),
    )
    signed_fake_valid = SignedTransaction(fake_tx_valid_txid, "cafebabe" * 16)
    fake_sig_dict = signed_fake_valid.to_dict()

    response = requests.post(
        f"http://127.0.0.1:{ALICE_NODE_PORT}/transactions",
        json=fake_sig_dict,
        timeout=5
    )
    if response.ok:
        print("   ⚠ PROBLEM: Transaction was accepted into mempool")
        print(f"   Response: {response.text}")
    else:
        print(f"   ✓ Transaction rejected by node - CORRECT")
        print(f"   Error: {response.status_code} - {response.text}")

    print("\n5. Mining a block to see if invalid transactions are rejected...")
    run_cmd(f"mine --node http://127.0.0.1:{ALICE_NODE_PORT}")

    print("\n6. Checking balances (should not include fake transactions)...")
    run_cmd(f"show alice --node http://127.0.0.1:{ALICE_NODE_PORT}")
    run_cmd(f"show bob --node http://127.0.0.1:{BOB_NODE_PORT}")


def main():
    print("\n" + "#" * 70)
    print("# FULL DEMO")
    print("#" * 70)
    clean_databases()

    try:
        demo_wallet()

        demo_transactions()

        demo_invalid_transactions()

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
