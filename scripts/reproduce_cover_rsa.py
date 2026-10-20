"""Replay 1033.jpg's historical RSA message with published factors.

Run from any directory: python scripts/reproduce_cover_rsa.py
Uses Python's standard library, reads a hash-pinned body, makes no network
requests, writes no files, and does not search for factors. This is a historical
compatibility decoder, not cryptographic software for new messages.
"""
from pathlib import Path
import base64
import hashlib
import json
import re
import zlib

ROOT = Path(__file__).resolve().parents[1]
P = 97513779050322159297664671238670850085661086043266591739338007321
Q = 77506098606928780021829964781695212837195959082370473820509360759
EXPECTED = b"\ncu343l33nqaekrnw.onion\n\n"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def mask(seed, length):
    """Crypt::RSA 1.99 DataFormat.pm uses counters 0, 20, 40, ... ."""
    return b"".join(
        hashlib.sha1(seed + counter.to_bytes(4, "big")).digest()
        for counter in range(0, length, 20)
    )[:length]


def xor(left, right):
    require(len(left) == len(right), "Mask length mismatch")
    return bytes(a ^ b for a, b in zip(left, right))


def reproduce():
    record = json.loads((ROOT / "data/evidence/illustrated-cover.json").read_text(
        encoding="utf-8"))["embedded_payload"]
    body = (ROOT / record["body_path"]).read_bytes()
    require(hashlib.sha256(body).hexdigest() == record["body_sha256"],
            "Message body differs from the verified extraction derivative")
    text = body.decode("ascii")
    exponent = int(re.search(r"^e = (\d+)$", text, re.M)[1])
    wrapped = re.search(r"^n = ([\d\\\s]+?)\n\n", text, re.M)[1]
    modulus = int(re.sub(r"\D", "", wrapped))
    require(exponent == 65537 and P * Q == modulus, "RSA parameters mismatch")
    width = (modulus.bit_length() + 7) // 8
    require(width == 54, "Unexpected RSA block width")
    phi = (P - 1) * (Q - 1)
    private_exponent = pow(exponent, -1, phi)
    require(exponent * private_exponent % phi == 1, "Inverse check failed")

    envelope = re.search(r"Scheme: Crypt::RSA::ES::OAEP\n\n(.*?)\n=([^\n]+)",
                         text, re.S)
    packed = base64.b64decode("".join(envelope[1].split()), validate=True)
    checksum = base64.b64decode(envelope[2], validate=True)
    require(hashlib.md5(packed).digest() == checksum, "Envelope checksum mismatch")
    # Input is pinned above. The historical frame is one length-prefixed field.
    frame = zlib.decompress(packed)
    name_size, data_size, rest = frame.split(b"\0", 2)
    require(name_size == b"10" and data_size == b"162", "Unexpected field lengths")
    require(rest[:10] == b"Cyphertext" and len(rest) == 172,
            "Unexpected content frame")
    ciphertext = rest[10:]
    blocks = []
    for offset in range(0, len(ciphertext), width):
        block = ciphertext[offset:offset + width]
        cipher_integer = int.from_bytes(block, "big")
        require(cipher_integer < modulus, "Ciphertext outside RSA modulus")
        decoded_integer = pow(cipher_integer, private_exponent, modulus)
        require(pow(decoded_integer, exponent, modulus) == cipher_integer,
                "RSA re-encryption failed")
        # This library encodes k-1 bytes; modern OAEP includes a leading zero.
        encoded = decoded_integer.to_bytes(width - 1, "big")
        masked_seed, masked_data = encoded[:20], encoded[20:]
        seed = xor(masked_seed, mask(masked_data, 20))
        data = xor(masked_data, mask(seed, len(masked_data)))
        require(data[:20] == hashlib.sha1(b"").digest(), "OAEP label hash mismatch")
        tail = data[20:]
        delimiter = next((i for i, value in enumerate(tail) if value), None)
        require(delimiter is not None and tail[delimiter] == 1,
                "OAEP padding delimiter missing")
        message = tail[delimiter + 1:]
        blocks.append({"block": offset // width + 1,
                       "ciphertext_hex": block.hex(),
                       "message_hex": message.hex(),
                       "rsa_round_trip": True})
    plaintext = b"".join(bytes.fromhex(b["message_hex"]) for b in blocks)
    require(plaintext == EXPECTED, "Historical plaintext control mismatch")
    return {"modulus_bits": modulus.bit_length(), "block_bytes": width,
            "body_sha256": record["body_sha256"], "blocks": blocks,
            "plaintext": plaintext.decode("ascii"),
            "plaintext_sha256": hashlib.sha256(plaintext).hexdigest(),
            "scope": "Published factors supplied; no factor discovery or service access"}


if __name__ == "__main__":
    print(json.dumps(reproduce(), indent=2))
