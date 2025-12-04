import subprocess
import sys
from pathlib import Path

PARENT_DIR = Path(__file__).parent.parent


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
    print("PART 2: TRANSACTION OPERATIONS")
    print("=" * 70)

    print("\n1. Initial account states...")
    run_cmd("show alice")
    run_cmd("show bob")

    print("\n2. Creating transaction: alice -> bob (25.0 coins)...")
    run_cmd("create-tx alice bob 25.0", password="demo123")

    print("\n3. Creating transaction: bob -> alice (10.0 coins)...")
    run_cmd("create-tx bob alice 10.0", password="demo123")

    print("\n4. Final account states...")
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
        sys.exit(1)


if __name__ == '__main__':
    main()
