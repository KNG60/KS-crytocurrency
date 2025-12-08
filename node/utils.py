import hashlib
import json
from typing import Any, Dict


def hash_dict(data: Dict[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
    # sha256 = 32 bytes * 2 chars/byte = 64 chars (1 byte = "f5")
    # digest = surowe 32 bajty, hexdigest = string representation of hex
