import os
import sqlite3
from typing import Any, Dict, List, Optional


class WalletStorage:
    """Single-wallet SQLite storage. Stores wallet metadata and its accounts in one DB file."""

    def __init__(self, wallet_db_path: str):
        base_dir = os.path.dirname(wallet_db_path)
        if base_dir:
            os.makedirs(base_dir, exist_ok=True)
        self.wallet_db_path = wallet_db_path
        self._init_wallet_db()

    def _connect(self):
        return sqlite3.connect(self.wallet_db_path)

    def _init_wallet_db(self):
        with self._connect() as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            # wallet_meta keeps one row with id=1
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS wallet_meta (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    label TEXT NOT NULL,
                    balance INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    verifier BLOB NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    label TEXT NOT NULL,
                    balance INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    address TEXT NOT NULL UNIQUE,
                    public_key_pem TEXT NOT NULL,
                    encrypted_private_key BLOB NOT NULL
                );
                """
            )
            conn.commit()

    # Wallet meta operations
    def init_wallet(self, label: str, created_at: str, verifier: bytes, balance: int = 0) -> None:
        """Initialize wallet metadata if not already present."""
        with self._connect() as conn:
            cur = conn.execute("SELECT 1 FROM wallet_meta WHERE id = 1")
            if cur.fetchone() is None:
                conn.execute(
                    "INSERT INTO wallet_meta (id, label, balance, created_at, verifier) VALUES (1, ?, ?, ?, ?)",
                    (label, balance, created_at, verifier),
                )
                conn.commit()

    def get_wallet(self) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT id, label, balance, created_at, verifier FROM wallet_meta WHERE id = 1"
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "label": row[1],
                "balance": row[2],
                "created_at": row[3],
                "verifier": row[4],
            }

    # Account operations
    def insert_account(
        self,
        label: str,
        created_at: str,
        address: str,
        public_key_pem: str,
        encrypted_private_key: bytes,
        balance: int = 0,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO accounts (label, balance, created_at, address, public_key_pem, encrypted_private_key)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    label,
                    balance,
                    created_at,
                    address,
                    public_key_pem,
                    encrypted_private_key,
                ),
            )
            conn.commit()
            return int(cur.lastrowid or 0)

    def list_accounts(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.execute(
                """
                SELECT id, label, balance, created_at, address
                FROM accounts
                ORDER BY id ASC
                """,
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "label": r[1],
                    "balance": r[2],
                    "created_at": r[3],
                    "address": r[4],
                }
                for r in rows
            ]
