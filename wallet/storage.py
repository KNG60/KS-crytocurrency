import os
import sqlite3
from getpass import getpass
from pathlib import Path

from .crypto import gen_key_pair

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


def get_db_path(label: str):
    wallet_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.join(wallet_dir, 'db')
    os.makedirs(db_dir, exist_ok=True)
    return Path(os.path.join(db_dir, f'{label}.db'))


def init_db(label: str) -> Path:
    db_path = get_db_path(label)

    with sqlite3.connect(db_path) as conn:
        conn.execute(schema_table)

    return db_path


def add_account(label: str, balance: float = 0.0):
    try:
        if abs(float(balance) - 0.0) > 1e-9:
            print(f"ERROR: New accounts must have a balance of 0.0. Provided: {balance}")
            return False
    except (TypeError, ValueError):
        print(f"ERROR: Invalid balance value: {balance}")
        return False

    db_path = get_db_path(label)

    with sqlite3.connect(db_path) as conn:
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


def delete_account(label: str):
    db_path = get_db_path(label)
    db_path.unlink()
    print(f"SUCCESS: Deleted account '{label}'")


def list_accounts():
    wallet_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = Path(os.path.join(wallet_dir, 'db'))

    if not db_dir.exists():
        print(f"INFO: No accounts found")
        return False

    db_files = list(db_dir.glob('*.db'))

    if not db_files:
        print(f"INFO: No accounts found")
        return False

    print(f"\n=== ACCOUNT LIST ===")
    for db_file in sorted(db_files):
        label = db_file.stem
        with sqlite3.connect(db_file) as conn:
            cur = conn.execute("SELECT id, label, balance, pubkey_hex, created_at FROM account WHERE label = ?",
                               (label,))
            row = cur.fetchone()
            if row:
                pub_short = row[3][:20] + "..." + row[3][-10:]
                print(f"[{row[0]}] {row[1]} | balance={row[2]} | pubkey={pub_short} | {row[4]}")
    return True


def get_account_details(label: str):
    db_path = get_db_path(label)

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "SELECT id, label, balance, pubkey_hex, created_at FROM account WHERE label = ?",
            (label,)
        )
        account = cur.fetchone()
        if account:
            return {
                'id': account[0],
                'label': account[1],
                'balance': account[2],
                'pubkey_hex': account[3],
                'created_at': account[4]
            }
        return None


def get_public_key(label: str):
    db_path = get_db_path(label)
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "SELECT pubkey_hex FROM account WHERE label = ?",
            (label,)
        )
        row = cur.fetchone()
        return row[0] if row else None


def get_private_key_pem(label: str):
    db_path = get_db_path(label)

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "SELECT privkey_pem FROM account WHERE label = ?",
            (label,)
        )
        row = cur.fetchone()

    if not row:
        print(f"INFO: Account '{label}' not found")
        return None

    return row[0]
