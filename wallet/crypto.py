from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def gen_key_pair(password: str) -> tuple[bytes, str]:
    priv = ec.generate_private_key(ec.SECP256K1())
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
    try:
        private_key = serialization.load_pem_private_key(
            pem_blob,
            password=password.encode('utf-8'),
        )
        return private_key
    except Exception as e:
        raise ValueError(f"Failed to decrypt private key: {e}")


def export_private_key_pem(private_key) -> str:
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    return priv_pem.decode('utf-8')
