import subprocess
import sys
from pathlib import Path

PARENT_DIR = Path(__file__).parent.parent

wallet_db_dir = PARENT_DIR / "wallet" / "db"
if wallet_db_dir.exists():
    for db_file in wallet_db_dir.glob("*.db"):
        db_file.unlink()
    print(f"Cleaned up previous databases")

print("=" * 60)
print("DEMO: Signed Transactions")
print("=" * 60)

print("\n1. Creating Alice's account...")
process = subprocess.Popen(
    [sys.executable, str(PARENT_DIR / "run_wallet.py"), "add", "alice"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    cwd=PARENT_DIR
)
stdout, stderr = process.communicate(input="alice123\n")
print(stdout)
if process.returncode != 0:
    print(f"Error: {stderr}")
    sys.exit(1)

print("\n2. Creating Bob's account...")
process = subprocess.Popen(
    [sys.executable, str(PARENT_DIR / "run_wallet.py"), "add", "bob"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    cwd=PARENT_DIR
)
stdout, stderr = process.communicate(input="bob456\n")
print(stdout)
if process.returncode != 0:
    print(f"Error: {stderr}")
    sys.exit(1)

print("\n3. Listing all accounts...")
result = subprocess.run(
    [sys.executable, str(PARENT_DIR / "run_wallet.py"), "list"],
    capture_output=True,
    text=True,
    check=True,
    cwd=PARENT_DIR
)
print(result.stdout)

print("4. Showing Alice's details...")
result = subprocess.run(
    [sys.executable, str(PARENT_DIR / "run_wallet.py"), "show", "alice"],
    capture_output=True,
    text=True,
    check=True,
    cwd=PARENT_DIR
)
print(result.stdout)

print("\n5. Creating transaction: Alice -> Bob (25 coins)...")
process = subprocess.Popen(
    [sys.executable, str(PARENT_DIR / "run_wallet.py"), "create-tx", "alice", "bob", "25.0"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    cwd=PARENT_DIR
)
stdout, stderr = process.communicate(input="alice123\n")
print(stdout)
if process.returncode != 0:
    print(f"Error: {stderr}")
    sys.exit(1)

print("\n" + "=" * 60)
print("Demo completed successfully!")
print("=" * 60)
