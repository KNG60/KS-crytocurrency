from getpass import getpass

from .crypto import decrypt_private_key, export_private_key_pem
from .storage import (
    DEFAULT_DB_NAME,
    get_account_details,
    get_private_key_pem
)


def show_private_key(label: str, db_name=DEFAULT_DB_NAME):
    pem_blob = get_private_key_pem(label, db_name)
    if pem_blob is None:
        return False

    password = getpass(f"Password to decrypt private key for account '{label}': ")
    try:
        private_key = decrypt_private_key(pem_blob, password)
        pem_str = export_private_key_pem(private_key)
        print(f"\n--- PRIVATE KEY PEM for {label} ---")
        print(pem_str)
        print("--- end ---\n")
        return True
    except ValueError as e:
        print(f"ERROR: {e}")
        return False


def show_account_details(label: str, db_name=DEFAULT_DB_NAME):
    account = get_account_details(label, db_name)
    if account:
        print(f"\n=== ACCOUNT DETAILS: {account['label']} ===")
        print(f"ID: {account['id']}")
        print(f"Balance: {account['balance']}")
        print(f"Public Key: {account['pubkey_hex']}")
        print(f"Created: {account['created_at']}")
        return True
    return False
