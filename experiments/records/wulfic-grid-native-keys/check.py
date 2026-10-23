"""Independently replay byte operations and the declared GP29 likelihood model."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx"
PRINTABLE = set(range(32, 127)) | {9, 10, 13}
MAGIC = {"PNG": b"\x89PNG", "JPEG": b"\xff\xd8\xff", "GIF": b"GIF8", "gzip": b"\x1f\x8b",
         "zip": b"PK\x03\x04", "bzip2": b"BZh", "PDF": b"%PDF", "ELF": b"\x7fELF",
         "PGP armour": b"-----BEGIN PGP"}


def byte_operation(grid: list[int], key: list[int], op: str) -> bytes:
    result = []
    for position, value in enumerate(grid):
        k = key[position % len(key)]
        result.append({"xor": value ^ k, "b-k": (value - k) % 256,
                       "b+k": (value + k) % 256}[op])
    return bytes(result)


def packet_length_fits(data: bytes) -> bool:
    if len(data) < 2 or data[0] < 128:
        return False
    if data[0] & 64:
        marker = data[1]
        if marker < 192:
            return marker == len(data) - 2
        if marker < 224 and len(data) >= 3:
            return (marker - 192) * 256 + data[2] + 192 == len(data) - 3
        return False
    size = (1, 2, 4, 0)[data[0] & 3]
    return bool(size and len(data) >= size + 1 and
                int.from_bytes(data[1:1 + size], "big") == len(data) - size - 1)


def signature(data: bytes) -> str:
    for name, prefix in MAGIC.items():
        if data.startswith(prefix):
            return name
    return "PGP packet" if packet_length_fits(data) else "-"


def score(cipher: list[int], key: list[int], q: list[float], mode: str, shift: int = 0) -> float:
    """Forward-sum three drift paths, normalizing after each rune."""
    ratios = [0.9 * 29 * frequency + 0.1 for frequency in q]
    state = {0: 1.0}
    total = 0.0
    for position, rune in enumerate(cipher):
        if position:
            next_state = {}
            for key_position, mass in state.items():
                for move, weight in ((0, .02), (1, .96), (2, .02)):
                    dest = key_position + move
                    next_state[dest] = next_state.get(dest, 0.0) + mass * weight
            state = next_state
        adjusted = {}
        for key_position, mass in state.items():
            if key_position >= len(key):
                emission = 1.0
            else:
                k = (key[key_position] + shift) % 29
                plain = {"sub": (rune - k) % 29, "add": (rune + k) % 29,
                         "beaufort": (k - rune) % 29}[mode]
                emission = ratios[plain]
            adjusted[key_position] = mass * emission
        normalizer = sum(adjusted.values())
        assert normalizer > 0
        total += math.log(normalizer)
        ceiling = max(adjusted.values()) * 1e-12
        state = {index: value / normalizer for index, value in adjusted.items()
                 if value >= ceiling}
    return total


def check() -> None:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert result["plan_sha256"] == hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest()
    for item in plan["inputs"]:
        assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    profile = json.loads((HERE / "source-profile.json").read_text(encoding="utf-8"))
    with (ROOT / "exports/alphanumeric-grids.csv").open(encoding="utf-8", newline="") as stream:
        tokens = [row["token"] for row in csv.DictReader(stream)]
    assert len(tokens) == 256 and all(len(token) == 2 for token in tokens)
    digits = [DIGITS.index(character) for token in tokens for character in token]
    grid = [digits[2 * i] * 60 + digits[2 * i + 1] for i in range(256)]
    assert grid == profile["grid_bytes"] and digits == profile["grid_digits"]
    with (HERE / "source-stage_n_results.tsv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    assert len(rows) == 456
    for row in rows:
        if row["reading"] == "bytes":
            data = grid if row["direction"] == "forward" else grid[::-1]
            output = byte_operation(data, profile["byte_keys"][row["key"]], row["op_or_mode"])
            assert row["printable"] == f"{sum(b in PRINTABLE for b in output) / len(output):.3f}"
            assert row["signature"] == signature(output)
            assert row["verdict"] == ("PASS" if float(row["printable"]) >= .90 or
                                      row["signature"] != "-" else "fail")
        else:
            c = [v % 29 for v in (grid if row["reading"] == "bytes mod 29" else digits)]
            if row["key"] == "constant":
                direction, _, shift_text = row["direction"].partition(" shift ")
                key, shift = [0] * len(c), int(shift_text)
            else:
                direction, key, shift = row["direction"], profile["rune_keys"][row["key"]], 0
            if direction == "reversed":
                c.reverse()
            actual = score(c, key, profile["unigram"], row["op_or_mode"], shift)
            assert f"{actual:.2f}" == row["log_lr_nats"], (row, actual)
            assert row["verdict"] == ("PASS" if actual >= 30 else "fail")
    assert all(row["verdict"] == "fail" for row in rows)
    # Post-replay detector diagnostics, not original preregistered controls.
    plain = b"A" * 256
    key = list(b"KEY")
    for op in ("xor", "b-k", "b+k"):
        if op == "xor":
            encoded = [value ^ key[i % len(key)] for i, value in enumerate(plain)]
        elif op == "b-k":
            encoded = [(value + key[i % len(key)]) % 256 for i, value in enumerate(plain)]
        else:
            encoded = [(value - key[i % len(key)]) % 256 for i, value in enumerate(plain)]
        assert byte_operation(encoded, key, op) == plain
    q = [.9] + [.1 / 28] * 28
    assert score([0] * 100, [0] * 100, q, "sub") > 30
    print("Independent grid reconstruction, all 456 source rows and post-replay detector diagnostics: OK")


if __name__ == "__main__":
    check()
