#!/usr/bin/env python3
"""Independent replay of Dukotah round28/L5 E-01w, from pinned input bytes."""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source"
RNG = random.Random(3301)
EXPONENTS = (65537, 3, 17)
VARIANTS = ("canon_256", "canon_256_decpref", "payload_resolved")
OIDS = {
    "SHA-1": "3021300906052b0e03021a05000414",
    "SHA-224": "302d300d060960864801650304020405001c",
    "SHA-256": "3031300d060960864801650304020105000420",
    "SHA-384": "3041300d060960864801650304020205000430",
    "SHA-512": "3051300d060960864801650304020305000440",
    "MD5": "3020300c06082a864886f70d020505000410",
}
HASHES = ("sha1", "sha256", "sha384", "sha512")
SALT_LENGTHS = (0, 20, 28, 32, 48, 64)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mgf1(seed: bytes, count: int, name: str) -> bytes:
    return b"".join(hashlib.new(name, seed + j.to_bytes(4, "big")).digest()
                    for j in range((count + hashlib.new(name).digest_size - 1)
                                   // hashlib.new(name).digest_size))[:count]


def recognize(block: bytes, bits: int = 431) -> list[dict]:
    """Replicate only the source's predeclared structural tiers, not message validity."""
    found = []
    if len(block) >= 11 and block[:2] == b"\x00\x01":
        pos = 2
        while pos < len(block) and block[pos] == 255:
            pos += 1
        if pos - 2 >= 8 and pos < len(block) and block[pos] == 0:
            tail = block[pos + 1:]
            label = next((name for name, prefix in OIDS.items()
                          if tail.startswith(bytes.fromhex(prefix))), None)
            found.append({"scheme": "pkcs1_v15_type1", "strict": label is not None,
                          "digest_info": label})
    if len(block) >= 11 and block[:2] == b"\x00\x02":
        pos = block.find(b"\x00", 2)
        if pos >= 10 and pos < len(block) - 1:
            found.append({"scheme": "pkcs1_v15_type2", "strict": False})
    for name in HASHES:
        hlen = hashlib.new(name).digest_size
        if len(block) < hlen + 2 or block[-1] != 188:
            continue
        db_length = len(block) - hlen - 1
        masked = block[:db_length]
        digest = block[db_length:-1]
        unmasked = bytearray(x ^ y for x, y in zip(masked, mgf1(digest, db_length, name)))
        unused = 8 * len(block) - bits
        if unused:
            unmasked[0] &= 255 >> unused
        for salt in dict.fromkeys((*SALT_LENGTHS, hlen)):
            pslen = len(block) - hlen - salt - 2
            if pslen >= 0 and unmasked[:pslen] == b"\x00" * pslen and unmasked[pslen] == 1:
                found.append({"scheme": "pss", "hash": name, "salt_len": salt,
                              "strict": pslen >= 8})
    return found


def scan(payload: bytes, modulus: int, exponents=EXPONENTS) -> dict:
    if len(payload) != 256 or modulus.bit_length() != 432:
        raise ValueError("Expected a 256-byte payload and the 432-bit pinned modulus")
    out = {"windows": 0, "direct_reads": 0, "modular_exponentiations": 0,
           "excluded_s_ge_n": 0, "strict_hits": [], "loose_hits": []}
    for offset in range(203):
        out["windows"] += 1
        for order, block in (("be", payload[offset:offset + 54]),
                             ("rev", payload[offset:offset + 54][::-1])):
            out["direct_reads"] += 1
            for finding in recognize(block):
                (out["strict_hits"] if finding["strict"] else out["loose_hits"]).append(
                    {"offset": offset, "order": order, "mode": "direct", "e": None,
                     "match": finding})
            candidate = int.from_bytes(block, "big")
            for exponent in exponents:
                if candidate >= modulus:
                    out["excluded_s_ge_n"] += 1
                    continue
                out["modular_exponentiations"] += 1
                representative = pow(candidate, exponent, modulus).to_bytes(54, "big")
                for finding in recognize(representative):
                    (out["strict_hits"] if finding["strict"] else out["loose_hits"]).append(
                        {"offset": offset, "order": order, "mode": "pow", "e": exponent,
                         "match": finding})
    return out


def prime(bits: int) -> int:
    while True:
        candidate = RNG.getrandbits(bits) | (1 << (bits - 1)) | 1
        if any(candidate % p == 0 for p in (3, 5, 7, 11, 13, 17, 19, 23, 29)):
            continue
        d = candidate - 1
        s = 0
        while d % 2 == 0:
            d //= 2
            s += 1
        for _ in range(32):
            a = RNG.randrange(2, candidate - 1)
            x = pow(a, d, candidate)
            if x in (1, candidate - 1):
                continue
            for __ in range(s - 1):
                x = x * x % candidate
                if x == candidate - 1:
                    break
            else:
                break
        else:
            return candidate


def plant_controls() -> dict:
    """Known-key examples go through the same 203-window scanner."""
    while True:
        p, q = prime(216), prime(216)
        n = p * q
        if p != q and n.bit_length() == 432 and (p - 1) * (q - 1) % 65537:
            break
    d = pow(65537, -1, (p - 1) * (q - 1))
    passed = {"pkcs1_v15_sha1": 0, "pss_sha1": 0}
    for kind, total in (("pkcs1_v15_sha1", 10), ("pss_sha1", 5)):
        for _ in range(total):
            msg = RNG.randbytes(32)
            if kind == "pkcs1_v15_sha1":
                di = bytes.fromhex(OIDS["SHA-1"]) + hashlib.sha1(msg).digest()
                em = b"\x00\x01" + b"\xff" * (54 - len(di) - 3) + b"\x00" + di
            else:
                salt = RNG.randbytes(20)
                h = hashlib.sha1(b"\x00" * 8 + hashlib.sha1(msg).digest() + salt).digest()
                db = b"\x00" * (54 - 20 - 20 - 2) + b"\x01" + salt
                mask = bytearray(x ^ y for x, y in zip(db, mgf1(h, len(db), "sha1")))
                mask[0] &= 127
                em = bytes(mask) + h + b"\xbc"
            signature = pow(int.from_bytes(em, "big"), d, n).to_bytes(54, "big")
            offset = RNG.randrange(203)
            buffer = bytearray(RNG.randbytes(256))
            buffer[offset:offset + 54] = signature
            hits = scan(bytes(buffer), n, (65537,))["strict_hits"]
            wanted = "pkcs1_v15_type1" if kind == "pkcs1_v15_sha1" else "pss"
            if any(row["offset"] == offset and row["order"] == "be" and
                   row["mode"] == "pow" and row["match"]["scheme"] == wanted for row in hits):
                passed[kind] += 1
    # Source used 200 random buffers. These test the same structural gate under
    # the known planted modulus, not the independence of natural manuscript bytes.
    random_strict = sum(len(scan(RNG.randbytes(256), n, (65537,))["strict_hits"])
                        for _ in range(200))
    return {"pkcs1_v15_sha1": {"recovered": passed["pkcs1_v15_sha1"], "planted": 10},
            "pss_sha1": {"recovered": passed["pss_sha1"], "planted": 5},
            "random_256_byte_buffers": 200, "random_strict_hits": random_strict}


def main() -> None:
    modulus_data = json.loads((SOURCE / "moduli.json").read_text(encoding="utf-8"))
    match = [v for v in modulus_data["other_moduli"] if v["name"] == "2013_puzzle"]
    if len(match) != 1:
        raise ValueError("Expected one named 2013 modulus")
    modulus = int(match[0]["n_hex"], 16)
    controls = plant_controls()
    if (controls["pkcs1_v15_sha1"]["recovered"] != 10 or
        controls["pss_sha1"]["recovered"] != 5 or controls["random_strict_hits"]):
        raise AssertionError("A planted or random-buffer gate failed; manuscript screen aborted")
    outcomes = {name: scan((SOURCE / (name + ".bin")).read_bytes(), modulus)
                for name in VARIANTS}
    report = {"schema": "liberpedia-rsa-window-54-replay-v1",
              "source_revision": "f08b20b632d91209ddbaa747e8e2f23df0c78ba1",
              "source_inputs_sha256": {p.name: file_hash(p) for p in sorted(SOURCE.iterdir()) if p.is_file()},
              "modulus_bits": modulus.bit_length(), "modulus_hex": hex(modulus)[2:],
              "exponents": list(EXPONENTS), "controls": controls, "variants": outcomes}
    (HERE / "results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                                       encoding="utf-8", newline="\n")
    print(json.dumps({"controls": controls,
                      "variants": {k: {field: v[field] for field in
                                     ("windows", "direct_reads", "modular_exponentiations",
                                      "excluded_s_ge_n", "strict_hits", "loose_hits")}
                                   for k, v in outcomes.items()}}, indent=2))


if __name__ == "__main__":
    main()
