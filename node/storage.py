import sqlite3
from typing import List, Dict


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

    def add_peer(self, host: str, port: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO peers (host, port) VALUES (?, ?) ON CONFLICT(host, port) DO NOTHING',
                (host, port)
            )
            conn.commit()

    def get_all_peers(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT id, host, port FROM peers ORDER BY id DESC'
            )
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def _row_to_dict(row) -> Dict:
        return {
            'id': row[0],
            'host': row[1],
            'port': row[2]
        }
