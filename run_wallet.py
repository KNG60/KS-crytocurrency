import argparse
import json
import sys

from wallet.commands import (
    show_account_details,
    show_private_key,
    create_transaction,
    mine_block,
)
from wallet.storage import (
    add_account,
    delete_account,
    list_accounts,
)


def parse_args():
    parser = argparse.ArgumentParser(description='Manage cryptocurrency wallet accounts')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    add_parser = subparsers.add_parser('add', help='Add a new account')
    add_parser.add_argument('label', help='Account label/name')

    subparsers.add_parser('list', help='List all accounts')

    delete_parser = subparsers.add_parser('delete', help='Delete an account')
    delete_parser.add_argument('label', help='Account label/name to delete')

    show_parser = subparsers.add_parser('show', help='Show details of specific account')
    show_parser.add_argument('label', help='Account label/name to show')
    show_parser.add_argument('--node', type=str, required=True,
                             help='Node URL to fetch balance (e.g., http://127.0.0.1:5000)')

    show_priv_parser = subparsers.add_parser('show-priv', help='Show decrypted private key (PEM) for account')
    show_priv_parser.add_argument('label', help='Account label/name to show private key for')

    tx_parser = subparsers.add_parser('create-tx', help='Create and sign a transaction')
    tx_parser.add_argument('sender', help='Sender account label')
    tx_parser.add_argument('recipient', help='Recipient account label')
    tx_parser.add_argument('amount', type=float, help='Amount to send')
    tx_parser.add_argument('--node', type=str, required=True,
                           help='Node URL to broadcast transaction (e.g., http://127.0.0.1:5000)')

    mine_parser = subparsers.add_parser('mine', help='Request mining from a node via HTTP')
    mine_parser.add_argument('--node', type=str, help='Node URL (e.g.: http://127.0.0.1:5000)')

    return parser.parse_args()


def main():
    args = parse_args()

    if args.command == 'add':
        add_account(args.label)
    elif args.command == 'list':
        list_accounts()
    elif args.command == 'delete':
        delete_account(args.label)
    elif args.command == 'show':
        show_account_details(args.label, node_url=args.node)
    elif args.command == 'show-priv':
        show_private_key(args.label)
    elif args.command == 'create-tx':
        create_transaction(args.sender, args.recipient, args.amount, node_url=args.node)
    elif args.command == 'mine':
        block_dict = mine_block(args.node)
        if block_dict:
            print("\nMined Block JSON:")
            print(json.dumps(block_dict, indent=2))
    else:
        print("No command specified. Use --help for available commands.")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
