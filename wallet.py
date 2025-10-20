#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sqlite3
import sys
from getpass import getpass
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

# Domyślna ścieżka do bazy danych
DEFAULT_DB_NAME = "account"
schema_table = """
CREATE TABLE IF NOT EXISTS account (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT UNIQUE NOT NULL,
    balance REAL NOT NULL DEFAULT 0.0,
    pubkey_hex TEXT NOT NULL,
    privkey_pem BLOB NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def get_db_path(name=DEFAULT_DB_NAME):
    """Zwraca ścieżkę do bazy danych na podstawie podanej nazwy."""
    return Path(f"db/{name}.db")


def init_db(name=DEFAULT_DB_NAME):
    """Inicjalizuje bazę danych jeśli nie istnieje.
    
    Args:
        name: Nazwa bazy danych (bez rozszerzenia .db)
    
    Returns:
        Path: Ścieżka do utworzonej bazy danych
    """
    # Określ ścieżkę do bazy danych
    db_path = get_db_path(name)
    
    # Upewnij się, że katalog db istnieje
    db_path.parent.mkdir(exist_ok=True)
    
    # Utwórz bazę danych i tabele
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_table)
    
    return db_path


def gen_key_pair(password: str):
    """Generates a secp256k1 key pair and returns (priv_pem, pub_hex)"""
    priv = ec.generate_private_key(ec.SECP256K1(), default_backend())
    pub = priv.public_key()
    pub_bytes = pub.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    pub_hex = pub_bytes.hex()
    enc = serialization.BestAvailableEncryption(password.encode("utf-8"))
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=enc
    )
    return priv_pem, pub_hex


def add_account(label: str, balance: float = 0.0, db_name=DEFAULT_DB_NAME):
    """Dodaje nowe konto do bazy danych."""
    # Only allow creating accounts with a zero balance
    try:
        # Use a small tolerance for float comparisons
        if abs(float(balance) - 0.0) > 1e-9:
            print(f"ERROR: New accounts must have a balance of 0.0. Provided: {balance}")
            return False
    except (TypeError, ValueError):
        print(f"ERROR: Invalid balance value: {balance}")
        return False

    db_path = get_db_path(db_name)
    with sqlite3.connect(db_path) as conn:
        try:
            password = getpass(f"Password to encrypt the private key for account '{label}': ")
            priv_pem, pub_hex = gen_key_pair(password)
            conn.execute(
                "INSERT INTO account (label, balance, pubkey_hex, privkey_pem) VALUES (?,?,?,?)",
                (label, balance, pub_hex, priv_pem)
            )
            conn.commit()
            print(f"SUCCESS: Added account '{label}' (balance {balance})")
            print(f"   pubkey_hex: {pub_hex[:20]}...{pub_hex[-10:]}")
            return True
        except sqlite3.IntegrityError:
            print(f"WARNING: Account '{label}' already exists.")
            return False


def delete_account(label: str, db_name=DEFAULT_DB_NAME):
    """Usuwa konto z bazy danych."""
    db_path = get_db_path(db_name)
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("DELETE FROM account WHERE label = ?", (label,))
        conn.commit()
        if cur.rowcount:
            print(f"SUCCESS: Deleted account '{label}'")
            return True
        else:
            print(f"INFO: Account '{label}' not found")
            return False


def list_accounts(db_name=DEFAULT_DB_NAME):
    """Wyświetla listę wszystkich kont z bazy danych."""
    db_path = get_db_path(db_name)
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("SELECT id, label, balance, pubkey_hex, created_at FROM account ORDER BY id ASC")
        rows = cur.fetchall()
    if not rows:
        print(f"INFO: No accounts in the database: {db_name}")
        return False
    else:
        print(f"\n=== ACCOUNT LIST ({db_name}) ===")
        for r in rows:
            pub_short = r[3][:20] + "..." + r[3][-10:]
            print(f"[{r[0]}] {r[1]} | balance={r[2]} | pubkey={pub_short} | {r[4]}")
        return True


def get_account_details(label: str, db_name=DEFAULT_DB_NAME):
    """Pobiera szczegóły konta o podanej nazwie."""
    db_path = get_db_path(db_name)
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "SELECT id, label, balance, pubkey_hex, created_at FROM account WHERE label = ?", 
            (label,)
        )
        account = cur.fetchone()
    
    if not account:
        print(f"INFO: Account '{label}' not found in database: {db_name}")
        return None
    
    return {
        'id': account[0],
        'label': account[1],
        'balance': account[2],
        'pubkey_hex': account[3],
        'created_at': account[4]
    }


def get_private_key_pem(label: str, db_name=DEFAULT_DB_NAME):
    """Pobiera zaszyfrowany PEM prywatnego klucza (BLOB) z bazy danych dla danego konta."""
    db_path = get_db_path(db_name)
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "SELECT privkey_pem FROM account WHERE label = ?",
            (label,)
        )
        row = cur.fetchone()

    if not row:
        print(f"INFO: Account '{label}' not found in database: {db_name}")
        return None

    return row[0]


def show_private_key(label: str, db_name=DEFAULT_DB_NAME):
    """Wyświetla odszyfrowany prywatny klucz PEM po podaniu hasła."""
    pem_blob = get_private_key_pem(label, db_name)
    if pem_blob is None:
        return False

    # Prosimy o hasło do odszyfrowania PEM
    password = getpass(f"Password to decrypt private key for account '{label}': ")
    try:
        private_key = serialization.load_pem_private_key(
            pem_blob,
            password=password.encode('utf-8'),
            backend=default_backend()
        )
    except Exception as e:
        print(f"ERROR: Failed to decrypt or load private key: {e}")
        return False

    # Wyeksportuj w czystym PEM bez szyfrowania i pokaż
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    print(f"\n--- PRIVATE KEY PEM for {label} ---")
    print(priv_pem.decode('utf-8'))
    print("--- end ---\n")
    return True


def parse_args():
    """Przetwarza argumenty wiersza poleceń."""
    parser = argparse.ArgumentParser(description='Manage cryptocurrency wallet accounts')
    
    # Dodaj globalny argument --name dla wszystkich komend
    parser.add_argument('--name', type=str, default=DEFAULT_DB_NAME, 
                       help=f'Database name (default: {DEFAULT_DB_NAME})')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Komenda init - inicjalizuje bazę danych
    init_parser = subparsers.add_parser('init', help='Initialize wallet database')
    
    # Komenda add - dodaje nowe konto
    add_parser = subparsers.add_parser('add', help='Add a new account')
    add_parser.add_argument('label', help='Account label/name')
    
    # Komenda list - wyświetla listę kont
    list_parser = subparsers.add_parser('list', help='List all accounts')
    
    # Komenda delete - usuwa konto
    delete_parser = subparsers.add_parser('delete', help='Delete an account')
    delete_parser.add_argument('label', help='Account label/name to delete')

    # Komenda show - wyświetla szczegóły konta
    show_parser = subparsers.add_parser('show', help='Show details of specific account')
    show_parser.add_argument('label', help='Account label/name to show')

    # Komenda show-priv - wyświetla odszyfrowany prywatny klucz PEM po podaniu hasła
    show_priv_parser = subparsers.add_parser('show-priv', help='Show decrypted private key (PEM) for account')
    show_priv_parser.add_argument('label', help='Account label/name to show private key for')
    
    return parser.parse_args()


def main():
    """Główna funkcja programu."""
    args = parse_args()
    
    # Uzyskaj nazwę bazy danych
    db_name = args.name
    
    if args.command == 'init':
        # Inicjalizacja bazy danych o podanej nazwie
        db_path = get_db_path(db_name)
        if db_path.exists():
            print(f"ERROR: Database already exists: {db_name}. Init aborted.")
            return 2
        db_path = init_db(db_name)
        print(f"SUCCESS: Wallet database initialized: {db_name}")
    elif args.command == 'add':
        # Dodanie konta do bazy danych (balance fixed to 0.0)
        add_account(args.label, 0.0, db_name)
    elif args.command == 'list':
        # Lista kont
        list_accounts(db_name)
    elif args.command == 'delete':
        # Usunięcie konta
        delete_account(args.label, db_name)
    elif args.command == 'show':
        # Wyświetlenie szczegółów konta
        account = get_account_details(args.label, db_name)
        if account:
            print(f"\n=== ACCOUNT DETAILS: {account['label']} ===")
            print(f"ID: {account['id']}")
            print(f"Balance: {account['balance']}")
            print(f"Public Key: {account['pubkey_hex']}")
            print(f"Created: {account['created_at']}")
    elif args.command == 'show-priv':
        # Wyświetlenie odszyfrowanego prywatnego klucza
        show_private_key(args.label, db_name)
    else:
        print("No command specified. Use --help for available commands.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())