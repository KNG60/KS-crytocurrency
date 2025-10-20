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
            print(f"✅ Added account '{label}' (balance {balance})")
            print(f"   pubkey_hex: {pub_hex[:20]}...{pub_hex[-10:]}")
            return True
        except sqlite3.IntegrityError:
            print(f"⚠️  Account '{label}' already exists.")
            return False


def delete_account(label: str, db_name=DEFAULT_DB_NAME):
    """Usuwa konto z bazy danych."""
    db_path = get_db_path(db_name)
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("DELETE FROM account WHERE label = ?", (label,))
        conn.commit()
        if cur.rowcount:
            print(f"🗑️  Deleted account '{label}'")
            return True
        else:
            print(f"ℹ️  Account '{label}' not found")
            return False


def list_accounts(db_name=DEFAULT_DB_NAME):
    """Wyświetla listę wszystkich kont z bazy danych."""
    db_path = get_db_path(db_name)
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("SELECT id, label, balance, pubkey_hex, created_at FROM account ORDER BY id ASC")
        rows = cur.fetchall()
    if not rows:
        print(f"📭 No accounts in the database: {db_path}")
        return False
    else:
        print(f"\n=== ACCOUNT LIST ({db_path}) ===")
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
        print(f"ℹ️  Account '{label}' not found in database: {db_path}")
        return None
    
    return {
        'id': account[0],
        'label': account[1],
        'balance': account[2],
        'pubkey_hex': account[3],
        'created_at': account[4]
    }


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
    add_parser.add_argument('--balance', type=float, default=0.0, help='Initial balance (default: 0.0)')
    
    # Komenda list - wyświetla listę kont
    list_parser = subparsers.add_parser('list', help='List all accounts')
    
    # Komenda delete - usuwa konto
    delete_parser = subparsers.add_parser('delete', help='Delete an account')
    delete_parser.add_argument('label', help='Account label/name to delete')

    # Komenda show - wyświetla szczegóły konta
    show_parser = subparsers.add_parser('show', help='Show details of specific account')
    show_parser.add_argument('label', help='Account label/name to show')
    
    return parser.parse_args()


def main():
    """Główna funkcja programu."""
    args = parse_args()
    
    # Uzyskaj nazwę bazy danych
    db_name = args.name
    
    if args.command == 'init':
        # Inicjalizacja bazy danych o podanej nazwie
        db_path = init_db(db_name)
        print(f"✅ Wallet database initialized: {db_path}")
    elif args.command == 'add':
        # Dodanie konta do bazy danych
        add_account(args.label, args.balance, db_name)
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
    else:
        print("No command specified. Use --help for available commands.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())