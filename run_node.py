import argparse
import logging

from node.server import NodeServer
from wallet.storage import get_public_key

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
    parser.add_argument('--role', type=str, choices=['normal', 'miner'], default='normal',
                        help='"normal" for regular node, "miner" for mining node')
    parser.add_argument('--wallet-label', type=str, required=True,
                        help='Label of account in wallet to use for public key')
    parser.add_argument('--centralized-manager', type=str, default=None,
                        help='URL of centralized graph manager (e.g., http://127.0.0.1:8080)')

    args = parser.parse_args()

    public_key = get_public_key(args.wallet_label)

    seed_peers = parse_seed_peers(args.seeds)

    server = NodeServer(
        host=args.host,
        port=args.port,
        seed_peers=seed_peers,
        role=args.role,
        public_key=public_key,
        centralized_manager_url=args.centralized_manager
    )

    server.run()


if __name__ == '__main__':
    main()
