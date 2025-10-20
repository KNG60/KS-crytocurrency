import base64
from typing import Optional, Tuple

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def generate_ec_keypair() -> Tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
    private_key = ec.generate_private_key(ec.SECP256K1())
    public_key = private_key.public_key()
    return private_key, public_key


def derive_key(passphrase: bytes, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase))


def serialize_private_key_encrypted(private_key: ec.EllipticCurvePrivateKey, passphrase: bytes, *, salt: Optional[bytes] = None) -> bytes:
    if salt is None:
        # For CLI/demo flows we may not have wallet salt at hand; use zero salt (not recommended for prod)
        salt = b"\x00" * 16
    k = derive_key(passphrase, salt)
    f = Fernet(k)
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return f.encrypt(pem)


def deserialize_private_key_encrypted(token: bytes, passphrase: bytes, *, salt: Optional[bytes] = None) -> ec.EllipticCurvePrivateKey:
    if salt is None:
        salt = b"\x00" * 16
    k = derive_key(passphrase, salt)
    f = Fernet(k)
    pem = f.decrypt(token)
    private_key = serialization.load_pem_private_key(pem, password=None)
    assert isinstance(private_key, ec.EllipticCurvePrivateKey)
    return private_key


def serialize_public_key(public_key: ec.EllipticCurvePublicKey) -> bytes:
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def sign_message(private_key: ec.EllipticCurvePrivateKey, message: bytes) -> bytes:
    signature = private_key.sign(message, ec.ECDSA(hashes.SHA256()))
    # Keep DER as is
    return signature


def verify_signature(public_key: ec.EllipticCurvePublicKey, message: bytes, signature: bytes) -> bool:
    try:
        public_key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
        return True
    except Exception:
        return False
