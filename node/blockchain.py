import hashlib
import json
import time
from typing import Dict, List, Optional


def _hash_dict(data: Dict) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class Block:
    def __init__(
        self,
        height: int,
        prev_hash: str,
        timestamp: int,
        txs: List[Dict],
        nonce: int,
        difficulty: int,
        miner: str,
        block_hash: str,
    ):
        self.height = height
        self.prev_hash = prev_hash
        self.timestamp = timestamp
        self.txs = txs or []
        self.nonce = nonce
        self.difficulty = difficulty
        self.miner = miner
        self.hash = block_hash

    def header(self) -> Dict:
        return {
            "height": self.height,
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp,
            "txs": self.txs,
            "nonce": self.nonce,
            "difficulty": self.difficulty,
            "miner": self.miner,
        }

    @staticmethod
    def compute_hash(header: Dict) -> str:
        return _hash_dict(header)

    def to_dict(self) -> Dict:
        return {
            "height": self.height,
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp,
            "txs": self.txs,
            "nonce": self.nonce,
            "difficulty": self.difficulty,
            "miner": self.miner,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "Block":
        return cls(
            height=int(d["height"]),
            prev_hash=str(d["prev_hash"]),
            timestamp=int(d["timestamp"]),
            txs=list(d.get("txs") or []),
            nonce=int(d["nonce"]),
            difficulty=int(d["difficulty"]),
            miner=str(d.get("miner", "")),
            block_hash=str(d["hash"]),
        )


class Blockchain:
    def __init__(self, difficulty: int):
        self.difficulty = max(0, int(difficulty))

    @staticmethod
    def is_pow_valid(h: str, difficulty: int) -> bool:
        return h.startswith("0" * max(0, int(difficulty)))

    def validate_block(self, block: Block, prev: Optional[Block]) -> bool:
        if block.height == 0:
            expected = Block.compute_hash(block.header())
            return block.prev_hash == "0" * 64 and block.hash == expected

        if prev is None:
            return False

        if block.height != prev.height + 1:
            return False
        if block.prev_hash != prev.hash:
            return False

        expected_hash = Block.compute_hash(block.header())
        if block.hash != expected_hash:
            return False

        if not self.is_pow_valid(block.hash, block.difficulty):
            return False

        return True

    def mine_next_block(self, prev: Block, miner_id: str, txs: Optional[List[Dict]] = None) -> Block:
        height = prev.height + 1
        nonce = 0
        while True:
            header = {
                "height": height,
                "prev_hash": prev.hash,
                "timestamp": int(time.time()),
                "txs": txs or [],
                "nonce": nonce,
                "difficulty": self.difficulty,
                "miner": miner_id,
            }
            h = Block.compute_hash(header)
            if self.is_pow_valid(h, self.difficulty):
                return Block(
                    height=height,
                    prev_hash=prev.hash,
                    timestamp=header["timestamp"],
                    txs=header["txs"],
                    nonce=nonce,
                    difficulty=self.difficulty,
                    miner=miner_id,
                    block_hash=h,
                )
            nonce += 1

    def create_genesis(self) -> Block:
        header = {
            "height": 0,
            "prev_hash": "0" * 64,
            "timestamp": int(time.time()),
            "txs": [],
            "nonce": 0,
            "difficulty": self.difficulty,
            "miner": "genesis",
        }
        h = Block.compute_hash(header)
        return Block(
            height=0,
            prev_hash=header["prev_hash"],
            timestamp=header["timestamp"],
            txs=[],
            nonce=0,
            difficulty=self.difficulty,
            miner="genesis",
            block_hash=h,
        )

    def validate_chain(self, chain: List[Dict]) -> bool:
        prev: Optional[Block] = None
        for b in chain:
            try:
                blk = Block.from_dict(b) if not isinstance(b, Block) else b
            except Exception:
                return False
            if not self.validate_block(blk, prev):
                return False
            prev = blk
        return True
