"""Independent Stage X4 grid, decoder and calibration checks."""
from __future__ import annotations

import bz2
import csv
import hashlib
import json
import lzma
import zlib
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx"
CODECS = ("zlib raw deflate", "zlib", "gzip", "bz2", "lzma auto")
ROUTES = ("R", "R reversed", "C", "C reversed")
CAP = 1 << 20


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_bytes() -> bytes:
    with (ROOT / "exports/alphanumeric-grids.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 256
    assert [int(r["sequence"]) for r in rows] == list(range(1, 257))
    return bytes(60 * DIGITS.index(r["token"][0]) + DIGITS.index(r["token"][1])
                 for r in rows if len(r["token"]) == 2)


def routes(grid: bytes) -> dict[str, bytes]:
    assert len(grid) == 256
    column = bytes(grid[row * 8 + col] for col in range(8) for row in range(32))
    return {"R": grid, "R reversed": grid[::-1], "C": column, "C reversed": column[::-1]}


def decode(codec: str, data: bytes) -> tuple[bool, int, str, bool]:
    """Single bounded decoder call; trailing input intentionally permitted."""
    if codec in {"zlib raw deflate", "zlib", "gzip"}:
        window = {"zlib raw deflate": -15, "zlib": 15, "gzip": 31}[codec]
        decoder = zlib.decompressobj(window)
        error = zlib.error
    elif codec == "bz2":
        decoder, error = bz2.BZ2Decompressor(), OSError
    elif codec == "lzma auto":
        decoder, error = lzma.LZMADecompressor(format=lzma.FORMAT_AUTO), lzma.LZMAError
    else:
        raise ValueError(codec)
    try:
        output = decoder.decompress(data, CAP)
    except error as exc:
        return False, 0, str(exc), False
    return bool(decoder.eof), len(output), "", bool(decoder.unused_data)


def source_signature(data: bytes) -> str:
    prefixes = {"PNG": b"\x89PNG", "JPEG": b"\xff\xd8\xff", "GIF": b"GIF8", "gzip": b"\x1f\x8b",
                "zip": b"PK\x03\x04", "bzip2": b"BZh", "PDF": b"%PDF", "ELF": b"\x7fELF",
                "PGP armour": b"-----BEGIN PGP"}
    for name, prefix in prefixes.items():
        if data.startswith(prefix):
            return name
    if len(data) < 2 or not data[0] & 0x80:
        return ""
    if data[0] & 0x40:
        first = data[1]
        if first < 192 and first == len(data) - 2:
            return "PGP packet"
        if 192 <= first < 224 and len(data) >= 3 and ((first - 192) << 8) + data[2] + 192 == len(data) - 3:
            return "PGP packet"
        return ""
    size = {0: 1, 1: 2, 2: 4}.get(data[0] & 3)
    return "PGP packet" if size and len(data) >= 1 + size and int.from_bytes(data[1:1 + size], "big") == len(data) - 1 - size else ""


def compressed(codec: str, message: bytes) -> bytes:
    if codec in {"zlib raw deflate", "zlib", "gzip"}:
        window = {"zlib raw deflate": -15, "zlib": 15, "gzip": 31}[codec]
        obj = zlib.compressobj(wbits=window)
        return obj.compress(message) + obj.flush()
    if codec == "bz2":
        return bz2.compress(message)
    return lzma.compress(message)


def diagnostic_controls() -> dict:
    message = b"LIBER PRIMUS GRID DECODER CONTROL " * 8
    report = {"complete": 0, "truncated": 0, "trailing_junk_accepted": 0}
    for codec in CODECS:
        packed = compressed(codec, message)
        complete = decode(codec, packed)
        truncated = decode(codec, packed[:-1])
        trailing = decode(codec, packed + b"EXTRA")
        assert complete[:2] == (True, len(message)) and not complete[3], codec
        assert not truncated[0], codec
        assert trailing[0] and trailing[3], codec
        report["complete"] += 1
        report["truncated"] += 1
        report["trailing_junk_accepted"] += 1
    return report


def audit() -> dict:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    assert sha((ROOT / plan["input"]["path"]).read_bytes()) == plan["input"]["sha256"]
    with (HERE / "source-stage_x4_rows.tsv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    assert len(rows) == 24 and all(r["part"] == "X4" for r in rows)
    table = {(r["reading"], r["test"]): r for r in rows}
    assert len(table) == 24
    grid = routes(grid_bytes())
    calibration: dict[str, int] = {}
    for codec in CODECS:
        rng = np.random.default_rng(3321)
        hits = 0
        for _ in range(10):
            blocks = rng.integers(0, 256, (10_000, 256), dtype=np.uint8)
            hits += sum(decode(codec, bytes(block))[0] for block in blocks)
        calibration[codec] = hits
        for route in ROUTES:
            row = table[route, codec]
            eof, length, error, _ = decode(codec, grid[route])
            assert row["value"] == f"eof={eof} out={length}"
            assert row["reference"] == f"chance {hits / 100_000:.5f}"
            assert row["detail"] == (error or "-")
            expected = "EXCLUDED" if not eof else ("PASS" if hits / 100_000 * 20 <= 0.01 else "inconclusive")
            assert row["verdict"] == expected
    for route in ROUTES:
        row = table[route, "stage N signatures"]
        sig = source_signature(grid[route])
        assert row["value"] == (sig or "-") and row["verdict"] == ("PASS" if sig else "EXCLUDED")
    controls = diagnostic_controls()
    return {"source_revision": plan["source"]["commit"], "grid_bytes": 256,
            "decoder_count": len(CODECS), "route_count": len(ROUTES),
            "decoder_tests": 20, "source_rows_including_signature": len(rows),
            "decoder_eof": sum(decode(c, b)[0] for b in grid.values() for c in CODECS),
            "signature_hits": sum(bool(source_signature(b)) for b in grid.values()),
            "null_draws_per_decoder": 100_000, "calibration_eof_hits": calibration,
            "post_replay_diagnostics": controls,
            "plan_sha256": sha((HERE / "plan.json").read_bytes())}
