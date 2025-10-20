from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from .crypto import (
    derive_key,
    deserialize_private_key_encrypted,
    generate_ec_keypair,
    serialize_private_key_encrypted,
    serialize_public_key,
)
from .db import WalletStorage


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


@dataclass
class AccountInfo:
    id: int
    label: str
    balance: int
    created_at: str
    address: str


class WalletManager:
    def __init__(self, db_path: str):
        self.storage = WalletStorage(db_path)
        self._unlocked = False
        self._passphrase_key = None

    def create_wallet(self, label: str, passphrase: str) -> None:
        # Initialize single-wallet DB with salt and a verifier derived from passphrase
        from os import urandom

        from cryptography.fernet import Fernet

        # No salt stored: passphrase alone (KDF) will be used to decrypt verifier later
        # still derive a key to create the verifier token
        salt = b""  # not stored
        k = derive_key(passphrase.encode("utf-8"), b"\x00" * 16)
        f = Fernet(k)
        verifier = f.encrypt(b"wallet-unlock")
        self.storage.init_wallet(label=label, created_at=now_iso(), verifier=verifier)

    def create_account(self, label: str, passphrase: str) -> AccountInfo:
        priv, pub = generate_ec_keypair()
        public_pem = serialize_public_key(pub).decode("utf-8")
        # Address: simplified as SHA256(pubkey_pem) hex, but keep short prefix for readability
        import hashlib

        h = hashlib.sha256(public_pem.encode("utf-8")).hexdigest()
        address = "ks" + h[:38]
        # Use passphrase-derived key with fixed zero salt (compatibility)
        enc_priv = serialize_private_key_encrypted(priv, passphrase.encode("utf-8"), salt=b"\x00" * 16)
        account_id = self.storage.insert_account(
            label=label,
            created_at=now_iso(),
            address=address,
            public_key_pem=public_pem,
            encrypted_private_key=enc_priv,
        )
        return AccountInfo(
            id=account_id,
            label=label,
            balance=0,
            created_at=now_iso(),
            address=address,
        )

    def unlock(self, passphrase: str) -> bool:
        """Verify passphrase by decrypting the verifier token. Sets unlocked state on success."""
        from cryptography.fernet import Fernet

        wallet = self.storage.get_wallet()
        if not wallet:
            return False
        verifier = wallet.get("verifier")
        if verifier is None:
            return False
        try:
            k = derive_key(passphrase.encode("utf-8"), b"\x00" * 16)
            f = Fernet(k)
            token = f.decrypt(verifier)
            if token == b"wallet-unlock":
                self._unlocked = True
                self._passphrase_key = k
                return True
            return False
        except Exception:
            return False

    def get_account_balance(self, *, account_id: int | None = None, address: str | None = None) -> int | None:
        """Return balance for an account by id or address. None if not found."""
        rows = self.storage.list_accounts()
        for r in rows:
            if account_id is not None and r["id"] == account_id:
                return r["balance"]
            if address is not None and r["address"] == address:
                return r["balance"]
        return None

    def list_accounts(self) -> List[AccountInfo]:
        rows = self.storage.list_accounts()
        return [AccountInfo(**row) for row in rows]  # type: ignore[arg-type]
