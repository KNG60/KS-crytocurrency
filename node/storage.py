import sqlite3
from typing import List, Dict, Tuple


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
