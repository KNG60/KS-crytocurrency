import time
from getpass import getpass

from node.transactions import Transaction
from .crypto import decrypt_private_key, export_private_key_pem, sign_tx
from .storage import (
    get_account_details,
    get_private_key_pem
)


def show_private_key(label: str):
    pem_blob = get_private_key_pem(label)
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


def show_account_details(label: str):
    account = get_account_details(label)
    if account:
        print(f"\n=== ACCOUNT DETAILS: {account['label']} ===")
        print(f"ID: {account['id']}")
        print(f"Balance: {account['balance']}")
        print(f"Public Key: {account['pubkey_hex']}")
        print(f"Created: {account['created_at']}")
        return True
    return False


def create_transaction(sender_label: str, recipient_label: str, amount: float):
    sender_account = get_account_details(sender_label)
    if not sender_account:
        print(f"ERROR: Sender account '{sender_label}' not found")
        return None

    recipient_account = get_account_details(recipient_label)
    if not recipient_account:
        print(f"ERROR: Recipient account '{recipient_label}' not found")
        return None

    sender_pubkey = sender_account['pubkey_hex']
    recipient_pubkey = recipient_account['pubkey_hex']

    try:
        amount = float(amount)
        if amount <= 0:
            print("ERROR: Amount must be positive")
            return None
    except ValueError:
        print("ERROR: Invalid amount")
        return None

    tx = Transaction(
        sender=sender_pubkey,
        recipient=recipient_pubkey,
        amount=amount,
        timestamp=int(time.time()),
        prev_txid=None
    )

    pem_blob = get_private_key_pem(sender_label)
    if pem_blob is None:
        print(f"ERROR: Cannot retrieve private key for '{sender_label}'")
        return None

    password = getpass(f"Password to decrypt private key for '{sender_label}': ")
    try:
        private_key = decrypt_private_key(pem_blob, password)
    except ValueError as e:
        print(f"ERROR: {e}")
        return None

    signed_tx = sign_tx(private_key, tx)

    print(f"\n=== TRANSACTION CREATED ===")
    print(f"TXID: {signed_tx.transaction.txid}")
    print(f"From: {sender_pubkey[:20]}...{sender_pubkey[-10:]}")
    print(f"To: {recipient_pubkey[:20]}...{recipient_pubkey[-10:]}")
    print(f"Amount: {amount}")
    print(f"Timestamp: {tx.timestamp}")
    print(f"Signature: {signed_tx.signature[:40]}...{signed_tx.signature[-20:]}")
    print("=========================\n")

    return signed_tx.to_dict()
