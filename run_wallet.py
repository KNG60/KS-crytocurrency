import argparse
import sys

from wallet.commands import show_account_details, show_private_key
from wallet.storage import (
    DEFAULT_DB_NAME,
    add_account,
    delete_account,
    get_db_path,
    init_db,
    list_accounts,
)


def parse_args():
    parser = argparse.ArgumentParser(description='Manage cryptocurrency wallet accounts')
    
    parser.add_argument('--name', type=str, default=DEFAULT_DB_NAME, 
                       help=f'Database name (default: {DEFAULT_DB_NAME})')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    subparsers.add_parser('init', help='Initialize wallet database')
    
    add_parser = subparsers.add_parser('add', help='Add a new account')
    add_parser.add_argument('label', help='Account label/name')
    
    subparsers.add_parser('list', help='List all accounts')
    
    delete_parser = subparsers.add_parser('delete', help='Delete an account')
    delete_parser.add_argument('label', help='Account label/name to delete')

    show_parser = subparsers.add_parser('show', help='Show details of specific account')
    show_parser.add_argument('label', help='Account label/name to show')

    show_priv_parser = subparsers.add_parser('show-priv', help='Show decrypted private key (PEM) for account')
    show_priv_parser.add_argument('label', help='Account label/name to show private key for')
    
    return parser.parse_args()

def main():
    args = parse_args()
    db_name = args.name
    db_path = get_db_path(db_name)

    if args.command is not None and args.command != 'init':
        if not db_path.exists():
            print(f"ERROR: Database does not exist: {db_name}. Run 'init' first.")
            return 2
    
    if args.command == 'init':
        if db_path.exists():
            print(f"ERROR: Database already exists: {db_name}. Init aborted.")
            return 2
        db_path = init_db(db_name)
        print(f"SUCCESS: Wallet database initialized: {db_name}")
    elif args.command == 'add':
        add_account(args.label, 0.0, db_name)
    elif args.command == 'list':
        list_accounts(db_name)
    elif args.command == 'delete':
        delete_account(args.label, db_name)
    elif args.command == 'show':
        show_account_details(args.label, db_name)
    elif args.command == 'show-priv':
        show_private_key(args.label, db_name)
    else:
        print("No command specified. Use --help for available commands.")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
