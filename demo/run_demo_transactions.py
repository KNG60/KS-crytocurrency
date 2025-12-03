import subprocess
import sys
from pathlib import Path

PARENT_DIR = Path(__file__).parent.parent

# Clean up previous demo database
demo_db_path = PARENT_DIR / "wallet" / "db" / "account.db"
if demo_db_path.exists():
    demo_db_path.unlink()
    print(f"Cleaned up previous database: {demo_db_path}")

print("=" * 60)
print("DEMO: Signed Transactions (Real CLI)")
print("=" * 60)

# Initialize database
print("\n1. Initializing wallet database...")
subprocess.run([sys.executable, str(PARENT_DIR / "run_wallet.py"), "init"], check=True, cwd=PARENT_DIR)

# Create Alice's account
print("\n2. Creating Alice's account...")
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

# Create Bob's account
print("3. Creating Bob's account...")
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

# Show accounts
print("\n4. Listing all accounts...")
result = subprocess.run(
    [sys.executable, str(PARENT_DIR / "run_wallet.py"), "list"],
    capture_output=True,
    text=True,
    check=True,
    cwd=PARENT_DIR
)
print(result.stdout)

# Show Alice details
print("5. Showing Alice's details...")
result = subprocess.run(
    [sys.executable, str(PARENT_DIR / "run_wallet.py"), "show", "alice"],
    capture_output=True,
    text=True,
    check=True,
    cwd=PARENT_DIR
)
print(result.stdout)

# Create transaction from Alice to Bob
print("\n6. Creating transaction: Alice -> Bob (25 coins)...")
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

print("\nTransaction created and signed!")
print("\nYou can:")
print("  - View accounts: python3 run_wallet.py list")
print("  - Show details: python3 run_wallet.py show alice")
print("  - Create another transaction: python3 run_wallet.py create-tx bob alice 10.0")
