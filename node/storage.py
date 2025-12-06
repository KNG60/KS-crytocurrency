import json
import sqlite3
from typing import Dict, List, Tuple

from node.blockchain import Block
from node.transactions import serialize_signed_transactions


class PeerStorage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS peers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    host TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    UNIQUE(host, port)
                )
            ''')
            conn.commit()

    def _execute_write(self, sql: str, params: Tuple):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(sql, params)
            conn.commit()

    def _fetch_all(self, sql: str, params: Tuple = ()) -> List[Tuple]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(sql, params)
            return cur.fetchall()

    def add_peer(self, host: str, port: int):
        self._execute_write(
            'INSERT INTO peers (host, port) VALUES (?, ?) ON CONFLICT(host, port) DO NOTHING',
            (host, port)
        )

    def remove_peer(self, host: str, port: int):
        self._execute_write(
            'DELETE FROM peers WHERE host = ? AND port = ?',
            (host, port)
        )

    def get_all_peers(self) -> List[Dict]:
        rows = self._fetch_all('SELECT host, port FROM peers ORDER BY id DESC')
        return [{'host': host, 'port': port} for host, port in rows]

    def count_peers(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute('SELECT COUNT(1) FROM peers')
            row = cur.fetchone()
            return int(row[0])


class ChainStorage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS blocks (
                    height INTEGER PRIMARY KEY,
                    prev_hash TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    txs_json TEXT NOT NULL,
                    nonce INTEGER NOT NULL,
                    difficulty INTEGER NOT NULL,
                    miner TEXT NOT NULL,
                    hash TEXT NOT NULL
                )
                '''
            )
            conn.commit()

    def save_block(self, block: Dict):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                INSERT OR IGNORE INTO blocks (height, prev_hash, timestamp, txs_json, nonce, difficulty, miner, hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    int(block["height"]),
                    str(block["prev_hash"]),
                    int(block["timestamp"]),
                    json.dumps(block.get("txs") or []),
                    int(block["nonce"]),
                    int(block["difficulty"]),
                    str(block.get("miner", "")),
                    str(block["hash"]),
                ),
            )
            conn.commit()

    def replace_chain(self, chain: List[Block]):

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            try:
                cur.execute('BEGIN')
                cur.execute('DELETE FROM blocks')
                for block in chain:
                    cur.execute(
                        '''
                        INSERT INTO blocks (height, prev_hash, timestamp, txs_json, nonce, difficulty, miner, hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''',
                        (
                            block.height,
                            block.prev_hash,
                            block.timestamp,
                            json.dumps(serialize_signed_transactions(block.txs)),
                            block.nonce,
                            block.difficulty,
                            block.miner,
                            block.hash,
                        ),
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def load_chain(self) -> List[Block]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                'SELECT height, prev_hash, timestamp, txs_json, nonce, difficulty, miner, hash FROM blocks ORDER BY height ASC'
            )
            rows = cur.fetchall()

        chain = []
        for r in rows:
            block_dict = {
                "height": int(r[0]),
                "prev_hash": r[1],
                "timestamp": int(r[2]),
                "txs": json.loads(r[3]),
                "nonce": int(r[4]),
                "difficulty": int(r[5]),
                "miner": r[6],
                "hash": r[7],
            }
            chain.append(Block.from_dict(block_dict))
        return chain

    def get_last_block(self) -> Dict | None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                'SELECT height, prev_hash, timestamp, txs_json, nonce, difficulty, miner, hash FROM blocks ORDER BY height DESC LIMIT 1'
            )
            row = cur.fetchone()
        if not row:
            return None
        return {
            "height": int(row[0]),
            "prev_hash": row[1],
            "timestamp": int(row[2]),
            "txs": json.loads(row[3]),
            "nonce": int(row[4]),
            "difficulty": int(row[5]),
            "miner": row[6],
            "hash": row[7],
        }
