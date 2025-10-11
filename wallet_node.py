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
DROP TABLE IF EXISTS account;
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

def add_user(label: str, balance: float = 0.0):
    with sqlite3.connect(DB_PATH) as conn:
        try:
            password = input(f"Password to encrypt the private key for '{label}': ")
            priv_pem, pub_hex = gen_key_pair(password)
            conn.execute(
                "INSERT INTO account (label, balance, pubkey_hex, privkey_pem) VALUES (?,?,?,?)",
                (label, balance, pub_hex, priv_pem)
            )
            conn.commit()
            print(f"✅ Added user '{label}' (balance {balance})")
            print(f"   pubkey_hex: {pub_hex[:20]}...{pub_hex[-10:]}")
        except sqlite3.IntegrityError:
            print(f"⚠️  User '{label}' already exists.")

def delete_user(label: str):
    with sqlite3.connect(DB_PATH) as conn:
        print(label)
        cur = conn.execute("DELETE FROM account WHERE label = ?", (label,))
        conn.commit()
        if cur.rowcount:
            print(f"🗑️  Deleted '{label}'")
        else:
            print(f"ℹ️  User '{label}' not found")

def list_users():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT id, label, balance, pubkey_hex, created_at FROM account ORDER BY id ASC")
        rows = cur.fetchall()
    if not rows:
        print("📭 No users in the database.")
    else:
        print("\n=== USER LIST ===")
        for r in rows:
            pub_short = r[3][:20] + "..." + r[3][-10:]
            print(f"[{r[0]}] {r[1]} | balance={r[2]} | pubkey={pub_short} | {r[4]}")

# --- TEST DEMO -------------------------------------------------------------

if __name__ == "__main__":
    print("=== DEMO WALLET ===")
    init_db()   
        # Add users
    add_user("Damian")
    add_user("Kacper")

    # Display the list
    list_users()

    # Delete one user
    delete_user("Kacper")

    # Display again
    list_users()
