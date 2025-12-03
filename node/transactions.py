from typing import Dict, List, Optional

from .utils import hash_dict


class Transaction:
    def __init__(
            self,
            sender: Optional[str],
            recipient: str,
            amount: float,
            timestamp: int,
            prev_txid: Optional[str] = None,
    ) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.prev_txid = prev_txid
        self.timestamp = timestamp

    def is_coinbase(self) -> bool:
        return self.sender is None

    @property
    def txid(self) -> str:
        return hash_dict({
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "prev_txid": self.prev_txid,
            "timestamp": self.timestamp,
        })

    def to_dict(self) -> Dict:
        return {
            "txid": self.txid,
            "timestamp": self.timestamp,
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "prev_txid": self.prev_txid,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Transaction":
        provided_txid = data["txid"]

        tx = cls(
            sender=str(data["sender"]) if data["sender"] is not None else None,
            recipient=str(data["recipient"]),
            amount=float(data["amount"]),
            timestamp=int(data["timestamp"]),
            prev_txid=str(data["prev_txid"]) if data["prev_txid"] is not None else None,
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


def serialize_transactions(txs: List[Transaction]) -> List[Dict]:
    return [tx.to_dict() for tx in txs]


def deserialize_transactions(raw: List[Dict]) -> List[Transaction]:
    return [Transaction.from_dict(tx) for tx in raw]
