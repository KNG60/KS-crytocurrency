import time
from getpass import getpass

import requests

from node.transactions import Transaction
from .crypto import decrypt_private_key, export_private_key_pem, sign_tx
from .storage import (
    get_account_details,
    get_private_key_pem
)


def calculate_balance_from_chain(pubkey_hex: str, node_url: str) -> float:
    try:
        response = requests.get(f"{node_url}/blocks", timeout=5)
        if response.status_code != 200:
            print(f"ERROR: Failed to fetch blockchain from {node_url}")
            return 0.0

        chain = response.json()
        balance = 0.0

        for block in chain:
            txs = block.get('txs', [])
            for tx in txs:
                recipient = tx['recipient']
                sender = tx['sender']
                amount = float(tx['amount'])

                if recipient == pubkey_hex:
                    balance += amount

                if sender == pubkey_hex:
                    balance -= amount

        return balance

    except requests.exceptions.ConnectionError:
        print(f"ERROR: Cannot connect to node at {node_url}")
        return 0.0
    except Exception as e:
        print(f"ERROR: Failed to calculate balance: {e}")
        return 0.0


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


def show_account_details(label: str, node_url: str):
    account = get_account_details(label)
    if account:
        print(f"\n=== ACCOUNT DETAILS: {account['label']} ===")
        print(f"ID: {account['id']}")
        balance = calculate_balance_from_chain(account['pubkey_hex'], node_url)
        print(f"Balance: {balance}")
        print(f"Public Key: {account['pubkey_hex']}")
        print(f"Created: {account['created_at']}")
        return True
    return False


def create_transaction(sender_label: str, recipient_label: str, amount: float, node_url: str):
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
    tx_dict = signed_tx.to_dict()

    print(f"\n=== TRANSACTION CREATED ===")
    print(f"TXID: {signed_tx.transaction.txid}")
    print(f"From: {sender_pubkey[:20]}...{sender_pubkey[-10:]}")
    print(f"To: {recipient_pubkey[:20]}...{recipient_pubkey[-10:]}")
    print(f"Amount: {amount}")
    print(f"Timestamp: {tx.timestamp}")
    print(f"Signature: {signed_tx.signature[:40]}...{signed_tx.signature[-20:]}")

    print(f"\nBroadcasting to node: {node_url}")
    try:
        response = requests.post(f"{node_url}/transactions", json=tx_dict, timeout=5)
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✓ Transaction broadcast successful!")
            print(f"Status: {result.get('status', 'accepted')}")
        else:
            print(f"✗ Transaction broadcast failed: {response.status_code}")
            print(f"Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print(f"✗ Cannot connect to node at {node_url}")
        print("Make sure the node is running")
    except Exception as e:
        print(f"✗ Broadcast error: {e}")

    print("=========================\n")

    return tx_dict


def mine_block(node_url: str):
    try:
        print(f"\n=== REQUESTING MINING FROM NODE ===")
        print(f"Node URL: {node_url}")
        print("Sending POST request to /mine...")

        start_time = time.time()
        response = requests.post(f"{node_url}/mine", timeout=120)
        elapsed = time.time() - start_time

        if response.status_code == 200:
            block_data = response.json()
            print(f"\n✓ Block mined successfully!")
            print(f"Block Hash: {block_data.get('hash')}")
            print(f"Block Height: {block_data.get('height')}")
            print(f"Nonce: {block_data.get('nonce')}")
            print(f"Miner: {block_data.get('miner', '')[:20]}...{block_data.get('miner', '')[-10:]}")
            print(f"Time taken: {elapsed:.2f} seconds")

            txs = block_data.get('txs', [])
            if txs:
                coinbase_tx = txs[0]
                print(f"Coinbase TX ID: {coinbase_tx.get('txid')}")
                print(f"Mining Reward: {coinbase_tx.get('amount')} coins")

            print("===================================\n")
            return block_data
        elif response.status_code == 403:
            print(f"\nERROR: Node is not configured as a miner")
            print("Start the node with --role miner to enable mining")
            return None
        else:
            print(f"\nERROR: Mining failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except requests.exceptions.ConnectionError:
        print(f"\nERROR: Cannot connect to node at {node_url}")
        print("Make sure the node is running (use run_node.py)")
        return None
    except requests.exceptions.Timeout:
        print(f"\nERROR: Mining request timed out")
        return None
    except Exception as e:
        print(f"\nERROR: {e}")
        return None
