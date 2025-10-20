#!/usr/bin/env python3
"""
Simple example/demo script for wallet operations
Shows all commands and their responses
"""

import os
import subprocess
import sys
from pathlib import Path

# Get parent directory (KS folder)
PARENT_DIR = Path(__file__).parent.parent

# Demo configuration
DEMO_DB = "demo_wallet"
DEMO_ACCOUNTS = ["alice", "bob", "charlie"]
DEMO_PASSWORD = "demo123"


def run_wallet_command(cmd):
    """Run a wallet command and display output"""
    full_cmd = f"py -3 run_wallet.py {cmd}"
    print("\n" + "="*70)
    print(f"COMMAND: {full_cmd}")
    print("="*70)
    
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, cwd=str(PARENT_DIR))
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    print(f"Exit Code: {result.returncode}")
    return result.returncode


def cleanup_demo_db():
    """Remove demo database"""
    db_path = PARENT_DIR / "db" / f"{DEMO_DB}.db"
    if db_path.exists():
        db_path.unlink()
        print(f"Cleaned up: {db_path}")


def main():
    """Run complete wallet demo"""
    print("\n" + "#"*70)
    print("# WALLET DEMO - All Operations")
    print("#"*70)
    print("\nTen skrypt demonstruje wszystkie operacje portfela:")
    print("  1. --help              - Wyswietlenie pomocy")
    print("  2. init                - Inicjalizacja bazy danych")
    print("  3. init (powtornie)    - Proba ponownej inicjalizacji (blad)")
    print("  4. add                 - Dodanie kont (alice, bob, charlie)")
    print("  5. list                - Wyswietlenie wszystkich kont")
    print("  6. show                - Wyswietlenie szczegolow konta")
    print("  7. show-priv           - Wyswietlenie klucza prywatnego")
    print("  8. show-priv (zle)     - Proba z blednym haslem (blad)")
    print("  9. delete              - Usuniecie konta")
    print(" 10. list (po usunieciu) - Wyswietlenie listy po usunieciu")
    print(" 11. list (brak bazy)    - Operacja na nieistniajacej bazie (blad)")
    print("\nHaslo uzyte w demo: " + DEMO_PASSWORD)
    print("#"*70 + "\n")
    
    input("Nacisnij ENTER aby kontynuowac...")
    
    # Cleanup any existing demo database
    cleanup_demo_db()
    
    # 1. Show help
    print("\n\n### 1. SHOW HELP ###")
    run_wallet_command("--help")
    
    # 2. Initialize database
    print("\n\n### 2. INITIALIZE DATABASE ###")
    run_wallet_command(f"--name {DEMO_DB} init")
    
    # 3. Try to initialize again (should fail)
    print("\n\n### 3. TRY TO INITIALIZE AGAIN (Should Fail) ###")
    run_wallet_command(f"--name {DEMO_DB} init")
    
    # 4. Add accounts
    print("\n\n### 4. ADD ACCOUNTS ###")
    for account in DEMO_ACCOUNTS:
        print(f"\n--- Adding account: {account} ---")
        # Create a process with input
        cmd = f"py -3 run_wallet.py --name {DEMO_DB} add {account}"
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
        if stderr:
            print("STDERR:", stderr)
        print(f"Exit Code: {proc.returncode}")
    
    # 5. List all accounts
    print("\n\n### 5. LIST ALL ACCOUNTS ###")
    run_wallet_command(f"--name {DEMO_DB} list")
    
    # 6. Show specific account details
    print("\n\n### 6. SHOW ACCOUNT DETAILS (alice) ###")
    run_wallet_command(f"--name {DEMO_DB} show alice")
    
    # 7. Show private key
    print("\n\n### 7. SHOW PRIVATE KEY (alice) ###")
    cmd = f"py -3 run_wallet.py --name {DEMO_DB} show-priv alice"
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
    if stderr:
        print("STDERR:", stderr)
    print(f"Exit Code: {proc.returncode}")
    
    # 8. Show private key with wrong password
    print("\n\n### 8. SHOW PRIVATE KEY WITH WRONG PASSWORD (Should Fail) ###")
    cmd = f"py -3 run_wallet.py --name {DEMO_DB} show-priv alice"
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
    if stderr:
        print("STDERR:", stderr)
    print(f"Exit Code: {proc.returncode}")
    
    # 9. Delete an account
    print("\n\n### 9. DELETE ACCOUNT (charlie) ###")
    run_wallet_command(f"--name {DEMO_DB} delete charlie")
    
    # 10. List accounts after deletion
    print("\n\n### 10. LIST ACCOUNTS AFTER DELETION ###")
    run_wallet_command(f"--name {DEMO_DB} list")
    
    # 11. Try operation on non-existent database
    print("\n\n### 11. TRY OPERATION ON NON-EXISTENT DATABASE (Should Fail) ###")
    run_wallet_command("--name nonexistent_db list")
    
    # Summary
    print("\n\n" + "#"*70)
    print("# DEMO COMPLETE")
    print("#"*70)
    print(f"\nDemo database created: db/{DEMO_DB}.db")
    print("Accounts created: alice, bob")
    print("Account deleted: charlie")
    print("\nTo cleanup, run:")
    print(f"  py -3 run_wallet.py --name {DEMO_DB} delete alice")
    print(f"  py -3 run_wallet.py --name {DEMO_DB} delete bob")
    print(f"  rm db/{DEMO_DB}.db")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        sys.exit(1)
