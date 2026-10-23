"""Independent scalar reconstruction of the pinned payload/key-skip sweep.

The source program uses NumPy and its own incremental quadgram scorer. This
checker parses the pinned rune and language-model inputs directly and rebuilds
the beam using plain Python. It checks every saved plaintext path, not just the
best score, and tests known full readings under the same search rule.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE / "source"
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
LABELS = ("F", "U", "TH", "O", "R", "C", "G", "W", "H", "N", "I", "J", "EO", "P", "X", "S", "T", "B", "E", "M", "L", "NG", "OE", "D", "A", "AE", "Y", "IA", "EA")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def score_model() -> tuple[dict[str, float], float]:
    counts = {}
    for line in (SOURCE / "data/english_quadgrams.txt").read_text(encoding="ascii").splitlines():
        key, count = line.split()
        counts[key] = int(count)
    total = sum(counts.values())
    return ({key: math.log10(value / total) for key, value in counts.items()},
            math.log10(0.01 / total))


def score(text: str, model: dict[str, float], floor: float) -> float:
    assert len(text) >= 4
    return sum(model.get(text[i:i + 4], floor) for i in range(len(text) - 3)) / (len(text) - 3)


def beam(cipher: list[int], key: list[int], sign: int,
         model: dict[str, float], floor: float) -> tuple[list[int], float]:
    """Same specified beam search, independently written without source imports."""
    length = len(cipher)
    if 4 * length + 8 > len(key):
        key = key + [0] * (4 * length + 8 - len(key))
    initial = (cipher[0] + sign * key[0]) % 29
    states = [(0.0, 0, LABELS[initial], (initial,))]
    for i in range(1, length):
        found = []
        for cumulative, pointer, text, path in states:
            for skipped in range(4):
                next_pointer = pointer + skipped + 1
                if next_pointer >= len(key):
                    break
                plain = (cipher[i] + sign * key[next_pointer]) % 29
                # Every bypassed key draw must have repeated the previous
                # ciphertext rune. This is the source's executable condition.
                if any((plain - sign * key[k]) % 29 != cipher[i - 1]
                       for k in range(pointer + 1, next_pointer)):
                    continue
                extension = text + LABELS[plain]
                delta = sum(model.get(extension[end - 4:end], floor)
                            for end in range(max(4, len(text) + 1), len(extension) + 1))
                found.append((cumulative + delta, next_pointer, extension, path + (plain,)))
        assert found, f"beam exhausted at rune {i}"
        found.sort(key=lambda state: state[0], reverse=True)
        states = found[:320]
    winner = max(states, key=lambda state: state[0])
    return list(winner[3]), score(winner[2], model, floor)


def source_pages() -> tuple[list[str], list[list[int]]]:
    raw = (SOURCE / "data/krisyotam_runes.txt").read_text(encoding="utf-8")
    pages = [[RUNES.index(ch) for ch in part if ch in RUNES] for part in raw.split("%")]
    pages = [page for page in pages if page][:-2]
    ids = [f"lp2-{page:02d}" for page in range(56) if page != 50]
    assert len(pages) == len(ids) == 55
    for identifier, page in zip(ids, pages):
        site = json.loads((ROOT / "data/pages" / f"{identifier}.json").read_text(encoding="utf-8"))
        assert page == [RUNES.index(ch) for ch in site["raw"] if ch in RUNES], identifier
    return ids, pages


def payloads() -> list[tuple[str, list[int]]]:
    out = []
    for name in ("canon_256.bin", "canon_256_decpref.bin"):
        raw = (SOURCE / "analysis/pp49_51" / name).read_bytes()
        assert len(raw) == 256
        out.append((name, [byte % 29 for byte in raw]))
        out.append((name + "~rev", [byte % 29 for byte in raw[::-1]]))
    return out


def encipher_plant(plain: list[int], key: list[int], sign: int) -> tuple[list[int], int]:
    rng = random.Random(3301)
    cipher = []
    pointer = 0
    skips = 0
    for value in plain:
        while True:
            candidate = (value - sign * key[pointer]) % 29
            if cipher and candidate == cipher[-1] and rng.random() < 0.83:
                pointer += 1
                skips += 1
                continue
            break
        cipher.append(candidate)
        pointer += 1
    return cipher, skips


def main() -> None:
    saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert sha(HERE / "plan-frozen.json") == saved["plan_sha256"]
    model, floor = score_model()
    ids, pages = source_pages()
    variants = payloads()
    rows = saved["rows"]
    assert len(rows) == 4 * 2 * 2 * 55 == saved["case_count"] == 880
    expected = []
    for name, base in variants:
        for sign in (-1, 1):
            for atbash in (0, 1):
                for index, original in enumerate(pages):
                    ciphertext = [28 - value for value in original] if atbash else original
                    key = base * (len(original) // 256 + 2) if len(original) > 256 else base
                    plain, measured = beam(ciphertext, key, sign, model, floor)
                    expected.append((name, sign, atbash, index, ids[index], len(original),
                                     measured, hashlib.sha256(bytes(plain)).hexdigest()))
    for row, (name, sign, atbash, index, identifier, length, measured, digest) in zip(rows, expected):
        assert (row["variant"], row["sign"], row["atbash"], row["source_page"],
                row["page_id"], row["runes"], row["plain_indices_sha256"]) == (
                name, sign, atbash, index, identifier, length, digest)
        assert abs(row["score"] - measured) < 1e-12
    best = max(rows, key=lambda row: row["score"])
    assert best == saved["best"]
    assert sum(row["score"] > -5.5 for row in rows) == saved["hit_count"] == 0
    assert best["page_id"] == "lp2-15" and abs(best["score"] + 6.756086107528059) < 1e-12

    reading = list(csv.DictReader((ROOT / "exports/readings/lp2-56.csv").open(encoding="utf-8-sig", newline="")))
    known = [int(row["output_index"]) for row in reading]
    assert len(known) == 85
    plants = []
    for name, base in variants:
        for sign in (-1, 1):
            key = base * 8
            planted, skips = encipher_plant(known, key, sign)
            for atbash in (0, 1):
                # The source applies Atbash before the beam, so store its
                # inverse as the synthetic manuscript input when atbash=1.
                stored = [28 - value for value in planted] if atbash else planted
                transformed = [28 - value for value in stored] if atbash else stored
                recovered, plant_score = beam(transformed, base, sign, model, floor)
                assert recovered == known and plant_score > -5.5
                plants.append((name, sign, atbash, skips, plant_score))
    assert len(plants) == 16
    assert not (SOURCE / "data/keys/mabinogion.txt").exists()
    print(f"PASS: {len(rows)} exact paths, 55 site page matches, 0 above bar; best {best['score']:.6f} on LP2-15")
    print("PASS: 16/16 complete planted known readings across payload, sign and Atbash settings")
    print("LIMIT: original generic wrong-key gate cannot run: missing mabinogion.txt")


if __name__ == "__main__":
    main()
