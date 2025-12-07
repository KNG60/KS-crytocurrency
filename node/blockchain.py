import time
from typing import Dict, List, Optional

from .transactions import (
    Transaction,
    SignedTransaction,
    serialize_signed_transactions,
    deserialize_signed_transactions,
    validate_transactions, COINBASE_SIGNATURE
)
from .utils import hash_dict

MINING_REWARD = 50.0


def calculate_balance(chain: List["Block"], public_key: str) -> float:
    balance = 0.0

    for block in chain:
        for signed_tx in block.txs:
            tx = signed_tx.transaction

            if tx.recipient == public_key:
                balance += tx.amount

            if tx.sender == public_key:
                balance -= tx.amount

    return balance


class Block:
    def __init__(
            self,
            height: int,
            prev_hash: str,
            timestamp: int,
            txs: List[SignedTransaction],
            nonce: int,
            difficulty: int,
            miner: str,
            block_hash: str,
    ):
        self.height = height
        self.prev_hash = prev_hash
        self.timestamp = timestamp
        self.txs = txs
        self.nonce = nonce
        self.difficulty = difficulty
        self.miner = miner
        self.hash = block_hash

    def header(self) -> Dict:
        return {
            "height": self.height,
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp,
            "txs": serialize_signed_transactions(self.txs),
            "nonce": self.nonce,
            "difficulty": self.difficulty,
            "miner": self.miner,
        }

    def to_dict(self) -> Dict:
        data = self.header()
        data["hash"] = self.hash
        return data

    @classmethod
    def from_dict(cls, d: Dict) -> "Block":
        return cls(
            height=int(d["height"]),
            prev_hash=str(d["prev_hash"]),
            timestamp=int(d["timestamp"]),
            txs=deserialize_signed_transactions(d["txs"]),
            nonce=int(d["nonce"]),
            difficulty=int(d["difficulty"]),
            miner=str(d["miner"]),
            block_hash=str(d["hash"]),
        )


class Blockchain:
    def __init__(self, difficulty: int):
        if difficulty <= 0:
            raise ValueError("Difficulty must be positive")
        self.difficulty = difficulty

    @staticmethod
    def is_pow_valid(h: str, difficulty: int) -> bool:
        return h.startswith("0" * max(0, int(difficulty)))

    @staticmethod
    def create_coinbase_transaction(recipient: str, amount: float = MINING_REWARD) -> SignedTransaction:
        transaction = Transaction(
            sender=None,
            recipient=recipient,
            amount=amount,
            timestamp=int(time.time()),
        )
        return SignedTransaction(transaction, signature=COINBASE_SIGNATURE)

    def validate_block(self, block: Block, prev: Optional[Block]) -> bool:
        if block.height == 0:
            expected = hash_dict(block.header())
            return block.prev_hash == "0" * 64 and block.hash == expected

        if prev is None:
            return False

        if block.height != prev.height + 1:
            return False
        if block.prev_hash != prev.hash:
            return False

        expected_hash = hash_dict(block.header())
        if block.hash != expected_hash:
            return False

        if not self.is_pow_valid(block.hash, block.difficulty):
            return False

        if not validate_transactions(block.txs, block.miner, MINING_REWARD):
            return False

        return True

    def mine_next_block(self, prev: Block, miner_id: str, txs: List[SignedTransaction]) -> Block:
        coinbase = self.create_coinbase_transaction(miner_id)
        all_txs = [coinbase] + txs

        height = prev.height + 1
        nonce = 0
        while True:
            block_data = {
                "height": height,
                "prev_hash": prev.hash,
                "timestamp": int(time.time()),
                "txs": serialize_signed_transactions(all_txs),
                "nonce": nonce,
                "difficulty": self.difficulty,
                "miner": miner_id,
            }
            h = hash_dict(block_data)
            block_data["hash"] = h
            if self.is_pow_valid(h, self.difficulty):
                return Block.from_dict(block_data)
            nonce += 1

    def create_genesis(self) -> Block:
        block_data = {
            "height": 0,
            "prev_hash": "0" * 64,
            "timestamp": 0,
            "txs": [],
            "nonce": 0,
            "difficulty": self.difficulty,
            "miner": "genesis",
        }
        h = hash_dict(block_data)
        block_data["hash"] = h
        return Block.from_dict(block_data)

    def validate_chain(self, chain: List["Block"]) -> bool:
        prev: Optional[Block] = None
        balances: Dict[str, float] = {}

        for blk in chain:
            if not self.validate_block(blk, prev):
                return False

            for signed_tx in blk.txs:
                tx = signed_tx.transaction

                if tx.sender:
                    sender_balance = balances.get(tx.sender, 0.0)
                    if sender_balance < tx.amount:
                        return False
                    balances[tx.sender] = sender_balance - tx.amount

                balances[tx.recipient] = balances.get(tx.recipient, 0.0) + tx.amount

            prev = blk
        return True
