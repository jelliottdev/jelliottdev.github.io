#!/usr/bin/env python3
"""Independent full-grid checker; does not import run.py or the source runner."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAMES = ("canon_256", "canon_256_decpref", "payload_resolved")
OIDS = (
    ("SHA-1", bytes.fromhex("3021300906052b0e03021a05000414")),
    ("SHA-224", bytes.fromhex("302d300d060960864801650304020405001c")),
    ("SHA-256", bytes.fromhex("3031300d060960864801650304020105000420")),
    ("SHA-384", bytes.fromhex("3041300d060960864801650304020205000430")),
    ("SHA-512", bytes.fromhex("3051300d060960864801650304020305000440")),
    ("MD5", bytes.fromhex("3020300c06082a864886f70d020505000410")),
)


def blob_sha(data: bytes) -> str:
    header = b"blob " + str(len(data)).encode() + b"\0"
    return hashlib.sha1(header + data).hexdigest()


def classify(frame: bytes) -> list[tuple]:
    """An alternate, standalone implementation of the published frame recognizer."""
    hit = []
    if len(frame) != 54:
        raise ValueError("All tested RSA representatives must be 54 bytes")
    if frame[0] == 0 and frame[1] == 1:
        stop = 2
        while stop < 54 and frame[stop] == 255:
            stop += 1
        if stop >= 10 and stop < 54 and frame[stop] == 0:
            suffix = frame[stop + 1:]
            label = next((name for name, prefix in OIDS if suffix[:len(prefix)] == prefix), None)
            hit.append(("pkcs1_v15_type1", label is not None, label, None))
    if frame[:2] == b"\0\2":
        zero = frame.find(b"\0", 2)
        if 10 <= zero < 53:
            hit.append(("pkcs1_v15_type2", False, None, None))
    if frame[53] == 188:
        for name in ("sha1", "sha256", "sha384", "sha512"):
            hlen = hashlib.new(name).digest_size
            if 54 < hlen + 2:
                continue
            db_len = 53 - hlen
            digest = frame[db_len:53]
            mask = bytearray()
            counter = 0
            while len(mask) < db_len:
                mask.extend(hashlib.new(name, digest + counter.to_bytes(4, "big")).digest())
                counter += 1
            db = bytearray(a ^ b for a, b in zip(frame[:db_len], mask))
            db[0] &= 127  # 431 encoded bits in a 54-byte representative
            for salt in dict.fromkeys((0, 20, 28, 32, 48, 64, hlen)):
                padding = 54 - hlen - salt - 2
                if padding >= 0 and db[:padding] == b"\0" * padding and db[padding] == 1:
                    hit.append(("pss", padding >= 8, name, salt))
    return hit


def all_cells(payload: bytes, modulus: int) -> tuple[dict, list]:
    totals = {"windows": 0, "direct_reads": 0, "modular_exponentiations": 0,
              "excluded_s_ge_n": 0}
    hits = []
    for start in range(0, len(payload) - 53):
        totals["windows"] += 1
        original = payload[start:start + 54]
        for direction, window in (("be", original), ("rev", bytes(reversed(original)))):
            totals["direct_reads"] += 1
            for typ, strict, label, salt in classify(window):
                hits.append((start, direction, "direct", None, typ, strict, label, salt))
            value = int.from_bytes(window, byteorder="big")
            for exponent in (65537, 3, 17):
                if value >= modulus:
                    totals["excluded_s_ge_n"] += 1
                    continue
                totals["modular_exponentiations"] += 1
                transformed = pow(value, exponent, modulus)
                frame = transformed.to_bytes(54, byteorder="big")
                for typ, strict, label, salt in classify(frame):
                    hits.append((start, direction, "pow", exponent, typ, strict, label, salt))
    return totals, hits


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    manifest = json.loads((HERE / "source-manifest.json").read_text(encoding="utf-8"))
    for row in manifest["files"]:
        actual = blob_sha((HERE / row["local"]).read_bytes())
        expect(actual == row["git_blob_sha1"], "Pinned source byte mismatch: " + row["local"])
    report = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    original = json.loads((HERE / "source/results.json").read_text(encoding="utf-8"))
    moduli = json.loads((HERE / "source/moduli.json").read_text(encoding="utf-8"))
    named = [item for item in moduli["other_moduli"] if item["name"] == "2013_puzzle"]
    expect(len(named) == 1, "Ambiguous named modulus")
    n = int(named[0]["n_hex"], 16)
    expect(n.bit_length() == 432 and report["modulus_hex"] == format(n, "x"), "Modulus mismatch")
    expect(report["source_revision"] == manifest["revision"], "Revision mismatch")
    for name in NAMES:
        data = (HERE / "source" / (name + ".bin")).read_bytes()
        expect(len(data) == 256, "Payload variant must have 256 bytes")
        totals, hits = all_cells(data, n)
        current = report["variants"][name]
        pinned = original["E-01w"][name]
        for field, number in totals.items():
            expect(current[field] == number, name + ": " + field)
        expect(totals == {"windows": 203, "direct_reads": 406,
                          "modular_exponentiations": 831, "excluded_s_ge_n": 387},
               name + ": unexpected grid cardinality")
        expect(pinned["evaluated_pow"] == totals["modular_exponentiations"] and
               pinned["excluded_s_ge_n"] == totals["excluded_s_ge_n"],
               name + ": pinned-source count mismatch")
        strict = [row for row in hits if row[5]]
        loose = [row for row in hits if not row[5]]
        expect(strict == [] and current["strict_hits"] == pinned["strict_hits"] == [],
               name + ": strict match discrepancy")
        expect(len(loose) == len(current["loose_hits"]) == pinned["loose_count"] == 1,
               name + ": loose match count")
        expect(loose[0] == (62, "be", "pow", 17, "pss", False, "sha256", 20),
               name + ": loose match location")
        local = current["loose_hits"][0]
        source = pinned["loose_rows"][0]
        expect((local["offset"], local["order"], local["mode"], local["e"],
                local["match"]["scheme"], local["match"]["strict"],
                local["match"].get("hash"), local["match"].get("salt_len")) == loose[0],
               name + ": local loose row")
        expect((source["offset"], source["order"], source["mode"], source["e"],
                source["match"]["scheme"], source["match"]["strict"],
                source["match"].get("hash"), source["match"].get("salt_len")) == loose[0],
               name + ": source loose row")
    controls = report["controls"]
    expect(controls["pkcs1_v15_sha1"] == {"recovered": 10, "planted": 10}, "Type-1 plant")
    expect(controls["pss_sha1"] == {"recovered": 5, "planted": 5}, "PSS plant")
    expect(controls["random_256_byte_buffers"] == 200 and
           controls["random_strict_hits"] == 0, "Random-buffer control")
    # Checker-specific positive and negative recognizer cases.
    digest = dict(OIDS)["SHA-1"] + hashlib.sha1(b"check").digest()
    frame = b"\0\1" + b"\xff" * (54 - len(digest) - 3) + b"\0" + digest
    expect(("pkcs1_v15_type1", True, "SHA-1", None) in classify(frame),
           "Independent recognizer failed a valid type-1 frame")
    expect(classify(b"\xff" * 54) == [], "Independent recognizer accepted an invalid frame")
    print("PASS: 9 pinned blobs, all 3 × 203 × 2 window orientations, 2,493 modular "
          "exponentiations, 1,218 direct reads, all match tiers and planted controls")


if __name__ == "__main__":
    main()
