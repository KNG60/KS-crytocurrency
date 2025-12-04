import subprocess
import sys
from pathlib import Path

PARENT_DIR = Path(__file__).parent.parent
DEMO_ACCOUNTS = ["alice", "bob", "charlie"]
DEMO_PASSWORD = "demo123"


def run_wallet_command(cmd):
    full_cmd = f"python run_wallet.py {cmd}"
    print("\n" + "=" * 70)
    print(f"COMMAND: {full_cmd}")
    print("=" * 70)
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, cwd=str(PARENT_DIR))
    if result.stdout:
        print(result.stdout)
    print(f"Exit Code: {result.returncode}")
    return result.returncode


def cleanup_demo_db():
    wallet_db_dir = PARENT_DIR / "wallet" / "db"
    if wallet_db_dir.exists():
        print(f"Cleaning wallet database directory: {wallet_db_dir}")
        for db_file in wallet_db_dir.glob("*.db"):
            db_file.unlink()
        print("  Wallet database directory cleaned successfully")


def main():
    print("\n" + "#" * 70)
    print("# WALLET DEMO - All Operations")
    print("#" * 70)
    print("\nTen skrypt demonstruje wszystkie operacje portfela:")
    print("  1. --help              - Wyswietlenie pomocy")
    print("  2. add                 - Dodanie kont (alice, bob, charlie)")
    print("  3. list                - Wyswietlenie wszystkich kont")
    print("  4. show                - Wyswietlenie szczegolow konta")
    print("  5. show-priv           - Wyswietlenie klucza prywatnego")
    print("  6. show-priv (zle)     - Proba z blednym haslem (blad)")
    print("  7. delete              - Usuniecie konta")
    print("  8. list (po usunieciu) - Wyswietlenie listy po usunieciu")
    print("  9. show (brak konta)   - Operacja na nieistniejacym koncie (blad)")
    print("\nHaslo uzyte w demo: " + DEMO_PASSWORD)
    print("#" * 70 + "\n")
    cleanup_demo_db()
    print("\n\n### 1. SHOW HELP ###")
    run_wallet_command("--help")
    print("\n\n### 2. ADD ACCOUNTS ###")
    for account in DEMO_ACCOUNTS:
        print(f"\n--- Adding account: {account} ---")
        cmd = f"python run_wallet.py add {account}"
        print(f"COMMAND: {cmd}")
        print(f"PASSWORD: {DEMO_PASSWORD}")
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(PARENT_DIR)
        )
        stdout, stderr = proc.communicate(input=f"{DEMO_PASSWORD}\n")
        print(stdout)
        print(f"Exit Code: {proc.returncode}")
    print("\n\n### 3. LIST ALL ACCOUNTS ###")
    run_wallet_command("list")
    print("\n\n### 4. SHOW ACCOUNT DETAILS (alice) ###")
    run_wallet_command("show alice")
    print("\n\n### 5. SHOW PRIVATE KEY (alice) ###")
    cmd = f"python run_wallet.py show-priv alice"
    print(f"COMMAND: {cmd}")
    print(f"PASSWORD: {DEMO_PASSWORD}")
    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(PARENT_DIR)
    )
    stdout, stderr = proc.communicate(input=f"{DEMO_PASSWORD}\n")
    print(stdout)
    print(f"Exit Code: {proc.returncode}")
    print("\n\n### 6. SHOW PRIVATE KEY WITH WRONG PASSWORD (Should Fail) ###")
    cmd = f"python run_wallet.py show-priv alice"
    print(f"COMMAND: {cmd}")
    print(f"PASSWORD: wrong_password")
    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(PARENT_DIR)
    )
    stdout, stderr = proc.communicate(input="wrong_password\n")
    print(stdout)
    print(f"Exit Code: {proc.returncode}")
    print("\n\n### 7. DELETE ACCOUNT (charlie) ###")
    run_wallet_command("delete charlie")
    print("\n\n### 8. LIST ACCOUNTS AFTER DELETION ###")
    run_wallet_command("list")
    print("\n\n### 9. TRY OPERATION ON NON-EXISTENT ACCOUNT (Should Fail) ###")
    run_wallet_command("show nonexistent")
    print("\n\n" + "#" * 70)
    print("# DEMO COMPLETE")
    print("#" * 70)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        sys.exit(1)
