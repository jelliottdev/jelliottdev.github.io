"""Bounded LP2 rail-fence test with visible word slots and fixed alignment controls."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PAGES = [f"lp2-{i:02}" for i in range(56)]
RAILS = tuple(range(2, 11))
TRIALS = 199
SEED = 3301


def rail_path(length: int, rails: int) -> list[int]:
    if rails < 2:
        raise ValueError(rails)
    period = 2 * (rails - 1)
    return [min(i % period, period - i % period) for i in range(length)]


def encrypt(values: list[int], rails: int) -> list[int]:
    path = rail_path(len(values), rails)
    return [v for row in range(rails) for v, r in zip(values, path) if r == row]


def decrypt(values: list[int], rails: int) -> list[int]:
    path = rail_path(len(values), rails)
    offsets = [0] * rails
    for row in path:
        offsets[row] += 1
    starts = [sum(offsets[:row]) for row in range(rails)]
    used = [0] * rails
    out = []
    for row in path:
        out.append(values[starts[row] + used[row]])
        used[row] += 1
    return out


def page_units(raw: str, alphabet: dict[str, int]) -> tuple[list[int], list[int]]:
    # Follow the source experiment: only hyphens define word slots; punctuation is ignored.
    blocks = raw.replace("/", "").replace("\n", "").split("-")
    words = [[alphabet[c] for c in block if c in alphabet] for block in blocks]
    words = [word for word in words if word]
    return [v for word in words for v in word], [len(word) for word in words]


def score(values: list[int], lengths: list[int], letters: list[str], lexicon: set[str]) -> int:
    offset = hits = 0
    for length in lengths:
        if length >= 3:
            word = "".join(letters[v] for v in values[offset:offset + length])
            hits += word in lexicon
        offset += length
    assert offset == len(values)
    return hits


def calculate() -> dict:
    index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
    alphabet = {row["rune"]: row["index"] for row in index["alphabet"]}
    letters = [row["latin"] for row in sorted(index["alphabet"], key=lambda row: row["index"])]
    # Use the published fixed English list; the source and transform are in SOURCE.txt.
    lexicon = {w for w in (HERE / "lexicon.txt").read_text(encoding="ascii").splitlines() if w}
    pages = [page_units((ROOT / f"text/{p}.txt").read_text(encoding="utf-8"), alphabet) for p in PAGES]
    direct = sum(score(vals, lengths, letters, lexicon) for vals, lengths in pages)
    observed = {str(rail): sum(score(decrypt(vals, rail), lengths, letters, lexicon)
                               for vals, lengths in pages) for rail in RAILS}
    best = max(observed.values())
    rng = random.Random(SEED)
    controls = []
    for _ in range(TRIALS):
        rotated = []
        for vals, lengths in pages:
            if len(vals) > 1:
                shift = rng.randrange(1, len(vals))
                rotated.append((vals[shift:] + vals[:shift], lengths))
            else:
                rotated.append((vals, lengths))
        controls.append(max(sum(score(decrypt(vals, rail), lengths, letters, lexicon)
                                for vals, lengths in rotated) for rail in RAILS))
    # The inverse is checked on actual solved runes, not only a toy alphabet.
    solved = page_units((ROOT / "text/lp1-03.txt").read_text(encoding="utf-8"), alphabet)[0]
    planted = {str(rail): decrypt(encrypt(solved, rail), rail) == solved for rail in RAILS}
    assert all(planted.values()) and sum(len(vals) for vals, _ in pages) > 12000
    paths = ["data/index.json", "text/lp1-03.txt", "experiments/records/rail-fence-visible-words/lexicon.txt"] + [f"text/{p}.txt" for p in PAGES]
    return {
        "schema": "liberpedia-rail-fence-visible-words-v1",
        "inputs_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        "pages": len(pages), "runes": sum(len(vals) for vals, _ in pages),
        "visible_word_slots": sum(len(lengths) for _, lengths in pages), "lexicon_size": len(lexicon),
        "direct_hits": direct, "rail_hits": observed, "best_rail_hits": best,
        "control_design": "199 seeded trials: rotate each page by a random nonzero offset, then select the best of the same nine rail counts",
        "control_seed": SEED, "control_best_hits": controls,
        "controls_at_least_observed": sum(x >= best for x in controls),
        "planted_inverse": planted,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = calculate()
    target = HERE / "results.json"
    if args.check:
        assert json.loads(target.read_text(encoding="utf-8")) == result
        print("rail-fence-visible-words: checked")
    else:
        target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({k: result[k] for k in ("runes", "visible_word_slots", "lexicon_size", "direct_hits", "rail_hits", "controls_at_least_observed")}, indent=2))


if __name__ == "__main__":
    main()
