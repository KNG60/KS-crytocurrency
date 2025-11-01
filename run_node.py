import argparse
import logging
import os

from node.server import NodeServer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def parse_seed_peers(seed_arg):
    if not seed_arg:
        return []

    peers = []
    for seed in seed_arg.split(','):
        seed = seed.strip()
        if ':' in seed:
            host, port = seed.rsplit(':', 1)
            peers.append({'host': host, 'port': int(port)})
    return peers


def main():
    parser = argparse.ArgumentParser(description='Run a blockchain node')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--seeds', type=str, default='',
                        help='Comma-separated seed peers (e.g., 127.0.0.1:5000,127.0.0.1:5001)')
    parser.add_argument('--role', type=str, choices=['full', 'miner'], default='full', help='Node role')
    parser.add_argument('--difficulty', type=int, default=4, help='PoW difficulty (leading hex zeros)')

    args = parser.parse_args()

    db_dir = "db"
    os.makedirs(db_dir, exist_ok=True)
    db_filename = f"peers_{args.port}.db"
    chain_db_filename = os.path.join(db_dir, f"chain_{args.port}.db")

    seed_peers = parse_seed_peers(args.seeds)

    server = NodeServer(
        host=args.host,
        port=args.port,
        db_path=os.path.join(db_dir, db_filename),
        seed_peers=seed_peers,
        chain_db_path=chain_db_filename,
        role=args.role,
        difficulty=args.difficulty
    )

    server.run()


if __name__ == '__main__':
    main()
