import argparse
import json
import sys

from wallet.commands import (
    show_account_details,
    show_private_key,
    create_transaction,
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

    show_priv_parser = subparsers.add_parser('show-priv', help='Show decrypted private key (PEM) for account')
    show_priv_parser.add_argument('label', help='Account label/name to show private key for')

    tx_parser = subparsers.add_parser('create-tx', help='Create and sign a transaction')
    tx_parser.add_argument('sender', help='Sender account label')
    tx_parser.add_argument('recipient', help='Recipient account label')
    tx_parser.add_argument('amount', type=float, help='Amount to send')

    return parser.parse_args()


def main():
    args = parse_args()

    if args.command == 'add':
        add_account(args.label, 0.0)
    elif args.command == 'list':
        list_accounts()
    elif args.command == 'delete':
        delete_account(args.label)
    elif args.command == 'show':
        show_account_details(args.label)
    elif args.command == 'show-priv':
        show_private_key(args.label)
    elif args.command == 'create-tx':
        tx_dict = create_transaction(args.sender, args.recipient, args.amount)
        if tx_dict:
            print("\nTransaction JSON:")
            print(json.dumps(tx_dict, indent=2))
    else:
        print("No command specified. Use --help for available commands.")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
