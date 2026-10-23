"""Replay the two supplied CC LP2-15–22 PDFs against archived rune streams.

This measures the reported construction and a small, explicit selection grid.
It does not implement a decryption or infer the historical key.
"""

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PANEL = [[3258, 3222, 3152, 3038],
         [3278, 3299, 3298, 2838],
         [3288, 3294, 3296, 2472],
         [4516, 1206, 708, 1820]]
LABELS = [[7, 8, 9, 10], [6, 1, 2, 11],
          [5, 4, 3, 12], [16, 15, 14, 13]]
RANKING = (4, 1, 5, 3, 6, 2, 7)
ROMAN = ((50, "L"), (40, "XL"), (10, "X"), (9, "IX"),
         (5, "V"), (4, "IV"), (1, "I"))
VALUE = {"I": 1, "V": 5, "X": 10, "L": 50}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rune_streams():
    alpha = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    gp = {entry["rune"]: entry["prime"] for entry in alpha}
    raw15 = (ROOT / "text/lp2-15.txt").read_text(encoding="utf-8")
    header, _, body = raw15.partition("\n")
    assert sum(c in gp for c in header) == 9
    streams = ["".join(c for c in body if c in gp),
               "".join(c for i in range(16, 23)
                       for c in (ROOT / f"text/lp2-{i:02}.txt").read_text(encoding="utf-8")
                       if c in gp)]
    return gp, streams


def spans_and_digits(stream, gp):
    digits = []
    spans = []
    for c in stream:
        start = len(digits) + 1
        digits.extend(str(gp[c]))
        spans.append((start, len(digits), c, gp[c]))
    return "".join(digits), spans


def spiral_addresses(n):
    assert n % 2 == 1
    row = col = n // 2
    result = {(row + 1, col + 1): 1}
    step = 1
    while len(result) < n * n:
        for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            for _ in range(step):
                if len(result) == n * n:
                    break
                row += dr
                col += dc
                result[(row + 1, col + 1)] = len(result) + 1
            if dr != 0:
                step += 1
    assert len(result) == n * n and result[(1, n)] == n * n
    return result


def contacts(n):
    addresses = spiral_addresses(n)
    remap = {1: 2, 2: 3, 3: n - 1, 4: n}
    return {label: addresses[(remap[r], remap[c])]
            for r, line in enumerate(LABELS, 1)
            for c, label in enumerate(line, 1)}


def boundary(address, spans):
    for start, end, rune, prime in spans:
        if start <= address <= end:
            return {"address": address, "rune": rune, "prime": prime,
                    "span": [start, end], "start": address == start,
                    "end": address == end}
    raise ValueError(address)


def roman(n):
    assert 1 <= n <= 99
    result = ""
    for value, token in ROMAN:
        while n >= value:
            result += token
            n -= value
    return result


def transforms(square):
    current = square
    for rotation in range(4):
        yield f"rotation-{rotation * 90}", current
        yield f"rotation-{rotation * 90}-reflection", [row[::-1] for row in current]
        current = [list(row) for row in zip(*current[::-1])]


def ordered_values(square):
    return {label: square[r - 1][c - 1]
            for r, line in enumerate(LABELS, 1)
            for c, label in enumerate(line, 1)}


def roman_selection(square, start, inverse=False):
    values = ordered_values(square)
    nums = [values[i] % 100 for i in range(start, start + 7)]
    if any(n == 0 for n in nums):
        return None
    initials = [roman(n)[0] for n in nums]
    if inverse:
        result = [initials[RANKING.index(i)] for i in range(1, 8)]
    else:
        result = [initials[i - 1] for i in RANKING]
    numbers = [VALUE[c] for c in result]
    return {"window": [start, start + 6], "source_entries": [values[i] for i in range(start, start + 7)],
            "last_two": nums, "initials": "".join(initials),
            "reordered": "".join(result), "sum": sum(numbers),
            "descending": numbers == sorted(numbers, reverse=True)}


def report():
    gp, streams = rune_streams()
    grids = {}
    for n, stream in zip((17, 59), streams):
        digits, spans = spans_and_digits(stream, gp)
        assert len(digits) == n * n
        address = contacts(n)
        observations = {str(i): boundary(address[i], spans) for i in range(1, 17)}
        expected = {str(i): (observations[str(i)]["start"] if i % 2 else observations[str(i)]["end"])
                    for i in range(1, 17)}
        grids[str(n)] = {"runes": len(stream), "digits": len(digits),
                         "addresses": address, "contacts": observations,
                         "start_end_matches": sum(expected.values()),
                         "start_end_by_position": expected,
                         "inner_edge": {str(i): observations[str(i)] for i in (9, 10, 11)}}
    search = []
    for name, square in transforms(PANEL):
        for start in range(1, 11):
            trial = roman_selection(square, start)
            if trial:
                search.append({"transform": name, **trial})
    hits = [entry for entry in search if entry["sum"] == 225 and entry["descending"]]
    transpose = [list(row) for row in zip(*PANEL)]
    focused = roman_selection(transpose, 5)
    inverse = roman_selection(transpose, 5, inverse=True)
    assert focused["source_entries"] == [3152, 3222, 3258, 3278, 3288, 4516, 1206]
    assert focused["reordered"] == "LLLLXXV" and focused["sum"] == 225
    assert grids["17"]["start_end_matches"] == 12
    assert grids["59"]["start_end_matches"] == 16
    return {"schema": "liberpedia-cc-stage-replay-v1",
            "source_sha256": {str(p.relative_to(ROOT)): sha(p) for p in
                              [ROOT / "data/index.json"] +
                              [ROOT / f"text/lp2-{i:02}.txt" for i in range(15, 23)]},
            "grids": grids, "focused_roman": focused, "inverse_roman": inverse,
            "printed_roman": roman_selection(PANEL, 5),
            "alternative_window": roman_selection(transpose, 6),
            "search": {"tested": len(search), "hits": hits},
            "limits": "Counts and contacts depend on the chosen representation, page grouping, spiral orientation and 1→2, 2→3, 3→N−1, 4→N registration. The proposed words and their Latin substitution were used to choose the extraction; there is no held-out plaintext test."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report()
    path = HERE / "results.json"
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not path.exists() or path.read_bytes() != encoded.encode("utf-8"):
            raise SystemExit("Saved results differ; rerun without --check and inspect the diff")
        print("CC Stage 1/2 replay checked")
    else:
        path.write_bytes(encoded.encode("utf-8"))
        print("Wrote", path)
