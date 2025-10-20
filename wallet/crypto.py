"""Crypto operations for wallet"""

from getpass import getpass

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def gen_key_pair(password: str):
    """Generates a secp256k1 key pair and returns (priv_pem, pub_hex)"""
    priv = ec.generate_private_key(ec.SECP256K1(), default_backend())
    pub = priv.public_key()
    pub_bytes = pub.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    pub_hex = pub_bytes.hex()
    enc = serialization.BestAvailableEncryption(password.encode("utf-8"))
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=enc
    )
    return priv_pem, pub_hex


def decrypt_private_key(pem_blob: bytes, password: str):
    """Decrypts and returns a private key from encrypted PEM blob"""
    try:
        private_key = serialization.load_pem_private_key(
            pem_blob,
            password=password.encode('utf-8'),
            backend=default_backend()
        )
        return private_key
    except Exception as e:
        raise ValueError(f"Failed to decrypt private key: {e}")


def export_private_key_pem(private_key) -> str:
    """Exports private key to unencrypted PEM format"""
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    return priv_pem.decode('utf-8')
