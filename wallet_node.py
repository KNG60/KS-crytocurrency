import argparse
import os
from pprint import pprint

from wallet.manager import WalletManager


def main():
    parser = argparse.ArgumentParser(description="Wallet utility")
    parser.add_argument("--label", type=str, default="Crypto Bro Wallet", help="Wallet label")
    parser.add_argument("--passphrase", type=str, default=None, help="Wallet bro-passphrase (or leave empty to prompt)")
    parser.add_argument("--accounts", type=int, default=1, help="How many accounts to create for demo")
    parser.add_argument("--balance-id", type=int, default=None, help="Show balance for account id")
    parser.add_argument("--balance-addr", type=str, default=None, help="Show balance for account address")
    args = parser.parse_args()

    slug = args.label.replace(" ", "_")
    wallet_db_path = os.path.join("db", f"wallet_{slug}.db")
    wm = WalletManager(wallet_db_path)
    # obtain passphrase securely if not provided as arg
    if args.passphrase is None:
        import getpass

        p = getpass.getpass("Passphrase for wallet: ")
    else:
        p = args.passphrase

    wm.create_wallet(args.label, p)
    print(f"Created wallet with label '{args.label}'")
    print(f"Wallet DB file: {wallet_db_path}")

    for i in range(args.accounts):
        acc = wm.create_account(f"Account {i+1}", p)
        print(f" - account #{acc.id} -> {acc.address}")

    print("\nAccounts:")
    for acc in wm.list_accounts():
        pprint(acc.__dict__)

    # optionally show balance
    if args.balance_id is not None or args.balance_addr is not None:
        # unlock first
        ok = wm.unlock(p)
        if not ok:
            print("Unable to unlock wallet with given passphrase")
        else:
            bal = wm.get_account_balance(account_id=args.balance_id, address=args.balance_addr)
            if bal is None:
                print("Account not found")
            else:
                print(f"Balance: {bal}")


if __name__ == "__main__":
    main()
