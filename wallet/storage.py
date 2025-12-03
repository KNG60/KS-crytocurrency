import os
import sqlite3
from getpass import getpass
from pathlib import Path

from .crypto import gen_key_pair

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
    wallet_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.join(wallet_dir, 'db')
    os.makedirs(db_dir, exist_ok=True)
    return Path(os.path.join(db_dir, f'{name}.db'))


def init_db(name=DEFAULT_DB_NAME) -> Path:
    db_path = get_db_path(name)

    with sqlite3.connect(db_path) as conn:
        conn.execute(schema_table)

    return db_path


def add_account(label: str, balance: float = 0.0, db_name=DEFAULT_DB_NAME):
    try:
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
