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
                    direction TEXT NOT NULL CHECK(direction IN ('inbound','outbound')),
                    UNIQUE(host, port, direction)
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

    def _add_peer(self, host: str, port: int, direction: str):
        self._execute_write(
            'INSERT INTO peers (host, port, direction) VALUES (?, ?, ?) ON CONFLICT(host, port, direction) DO NOTHING',
            (host, port, direction)
        )

    def _remove_peer(self, host: str, port: int, direction: str):
        self._execute_write(
            'DELETE FROM peers WHERE host = ? AND port = ? AND direction = ?',
            (host, port, direction)
        )

    def _get_peers(self, direction: str) -> List[Dict]:
        rows = self._fetch_all(
            'SELECT id, host, port FROM peers WHERE direction = ? ORDER BY id DESC',
            (direction,)
        )
        return [{'host': host, 'port': port} for host, port in rows]

    def _count_peers(self, direction: str) -> int:
        rows = self._fetch_all('SELECT COUNT(1) FROM peers WHERE direction = ?', (direction,))
        row = rows[0] if rows else None
        return int(row[0]) if row else 0

    def add_inbound_peer(self, host: str, port: int):
        self._add_peer(host, port, 'inbound')

    def add_outbound_peer(self, host: str, port: int):
        self._add_peer(host, port, 'outbound')

    def remove_inbound_peer(self, host: str, port: int):
        self._remove_peer(host, port, 'inbound')

    def get_inbound_peers(self) -> List[Dict]:
        return self._get_peers('inbound')

    def count_inbound_peers(self) -> int:
        return self._count_peers('inbound')

    def get_all_peers(self) -> List[Dict]:
        rows = self._fetch_all('SELECT host, port FROM peers')
        unique_peers = {(host, port) for host, port in rows}
        return [{'host': host, 'port': port} for host, port in unique_peers]
