#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sqlite3
from getpass import getpass
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

DB_PATH = Path("db/account.db")
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


def init_db():
    # Sprawdź, czy baza danych istnieje
    db_file = Path(DB_PATH)
    db_file.parent.mkdir(exist_ok=True)  # Upewnij się, że katalog db istnieje
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(schema_table)

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

def add_account(label: str, balance: float = 0.0):
    with sqlite3.connect(DB_PATH) as conn:
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
        except sqlite3.IntegrityError:
            print(f"⚠️  Account '{label}' already exists.")

def delete_account(label: str):
    with sqlite3.connect(DB_PATH) as conn:
        print(label)
        cur = conn.execute("DELETE FROM account WHERE label = ?", (label,))
        conn.commit()
        if cur.rowcount:
            print(f"🗑️  Deleted account '{label}'")
        else:
            print(f"ℹ️  Account '{label}' not found")

def list_accounts():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT id, label, balance, pubkey_hex, created_at FROM account ORDER BY id ASC")
        rows = cur.fetchall()
    if not rows:
        print("📭 No accounts in the database.")
    else:
        print("\n=== ACCOUNT LIST ===")
        for r in rows:
            pub_short = r[3][:20] + "..." + r[3][-10:]
            print(f"[{r[0]}] {r[1]} | balance={r[2]} | pubkey={pub_short} | {r[4]}")

# --- TEST DEMO -------------------------------------------------------------

if __name__ == "__main__":
    print("=== DEMO WALLET ===")
    init_db()   
        # Add accounts
    add_account("Damian")
    add_account("Kacper")

    # Display the list
    list_accounts()

    # Delete one account
    delete_account("Kacper")

    # Display again
    list_accounts()
