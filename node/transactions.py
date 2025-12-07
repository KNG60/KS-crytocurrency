from typing import Dict, List, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from .utils import hash_dict

COINBASE_SIGNATURE = "COINBASE"


class Transaction:
    def __init__(
            self,
            sender: Optional[str],
            recipient: str,
            amount: float,
            timestamp: int,
    ) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.timestamp = timestamp

    @property
    def txid(self) -> str:
        return hash_dict({
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "timestamp": self.timestamp,
        })

    def to_dict(self) -> Dict:
        return {
            "txid": self.txid,
            "timestamp": self.timestamp,
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Transaction":
        provided_txid = data["txid"]

        tx = cls(
            sender=str(data["sender"]) if data["sender"] is not None else None,
            recipient=str(data["recipient"]),
            amount=float(data["amount"]),
            timestamp=int(data["timestamp"]),
        )

        if provided_txid and str(provided_txid) != tx.txid:
            raise ValueError(f"Invalid txid: expected {tx.txid}, got {provided_txid}")

        return tx


class SignedTransaction:
    def __init__(self, transaction: Transaction, signature: str):
        self.transaction = transaction
        self.signature = signature

    def to_dict(self) -> Dict:
        tx_dict = self.transaction.to_dict()
        tx_dict["signature"] = self.signature
        return tx_dict

    @classmethod
    def from_dict(cls, data: Dict) -> "SignedTransaction":
        signature = data["signature"]
        transaction = Transaction.from_dict(data)
        signed_tx = cls(transaction, signature)

        if not verify_signature(signed_tx):
            raise ValueError(f"Invalid signature for transaction {transaction.to_dict()}")

        return signed_tx


def serialize_signed_transactions(txs: List[SignedTransaction]) -> List[Dict]:
    return [tx.to_dict() for tx in txs]


def deserialize_signed_transactions(raw: List[Dict]) -> List[SignedTransaction]:
    return [SignedTransaction.from_dict(tx) for tx in raw]


def verify_signature(signed_tx: SignedTransaction) -> bool:
    public_key_hex = signed_tx.transaction.sender
    if public_key_hex is None:
        return signed_tx.signature == COINBASE_SIGNATURE

    pub_bytes = bytes.fromhex(public_key_hex)
    pub_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), pub_bytes)
    signature_bytes = bytes.fromhex(signed_tx.signature)
    try:
        pub_key.verify(
            signature_bytes,
            signed_tx.transaction.txid.encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )
    except InvalidSignature:
        return False
    return True


def validate_transactions(txs: List[SignedTransaction], miner: str, mining_reward: float) -> bool:
    if len(txs) == 0:
        return True

    first_tx = txs[0].transaction
    if first_tx.sender is not None:
        return False
    if first_tx.recipient != miner:
        return False
    if first_tx.amount != mining_reward:
        return False

    for signed_tx in txs[1:]:
        if not verify_signature(signed_tx):
            return False

    return True
