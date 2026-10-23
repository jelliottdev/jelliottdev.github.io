"""Test four fixed pairwise readings of the published 1,894-rune equality."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
A_PAGES = [f"lp1-{n:02}" for n in range(6, 17)]
B_PAGES = [f"lp2-{n:02}" for n in range(15, 23)]
INPUTS = ["data/index.json", "data/source-snapshots/lp-rune-counts-2026-10-22.csv"] + [
    f"text/{page}.txt" for page in A_PAGES + B_PAGES
]


def section(page: str, part: int | None, alphabet: dict[str, int]) -> list[int]:
    raw = (ROOT / f"text/{page}.txt").read_text(encoding="utf-8")
    pieces = [[alphabet[c] for c in piece if c in alphabet] for piece in raw.split("&")]
    pieces = [piece for piece in pieces if piece]
    if part is not None:
        assert len(pieces) == 2
        return pieces[part]
    return [value for piece in pieces for value in piece]


def pair_score(a: list[int], b: list[int], reverse: bool, subtract: bool, shift: int) -> int:
    counts = [0] * 29
    n = len(a)
    if reverse:
        for i, value in enumerate(a):
            other = b[n - 1 - ((i + shift) % n)]
            counts[((other - value) if subtract else (other + value)) % 29] += 1
    else:
        for i, value in enumerate(a):
            other = b[(i + shift) % n]
            counts[((other - value) if subtract else (other + value)) % 29] += 1
    return sum(count * (count - 1) for count in counts)


def calculate() -> dict:
    index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
    alphabet = {row["rune"]: row["index"] for row in index["alphabet"]}
    assert len(alphabet) == 29 and alphabet["ᚠ"] == 0
    a = [value for page in A_PAGES for value in section(page, 0 if page == "lp1-16" else None, alphabet)]
    a = [value for value in a if value != 0]
    b = [value for page in B_PAGES for value in section(page, 1 if page == "lp2-15" else None, alphabet)]
    assert len(a) == len(b) == 1894
    variants = [("add", False, False), ("subtract", False, True),
                ("reverse-add", True, False), ("reverse-subtract", True, True)]
    scores = []
    for shift in range(len(a)):
        row = {name: pair_score(a, b, reverse, subtract, shift)
               for name, reverse, subtract in variants}
        scores.append({"shift": shift, "best": max(row.values()), "variant_scores": row} if shift == 0
                      else {"shift": shift, "best": max(row.values())})
    observed = scores[0]["best"]
    controls = [row["best"] for row in scores[1:]]
    tail = sum(value >= observed for value in controls)
    input_hashes = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in INPUTS}
    n = len(a)
    return {
        "schema": "liberpedia-section-1894-pairing-v1",
        "input_sha256": input_hashes,
        "construction": "A: LP1-06–15 plus first section of LP1-16, omitting every F. B: second section of LP2-15 plus LP2-16–22, F retained.",
        "length": n,
        "ordered_pair_denominator": n * (n - 1),
        "variants": scores[0]["variant_scores"],
        "observed_best": observed,
        "observed_ioc": round(observed / (n * (n - 1)), 8),
        "nonzero_shift_count": len(controls),
        "nonzero_shifts_at_least_observed": tail,
        "conditional_fraction": f"{tail + 1}/{n}",
        "control_best_min": min(controls),
        "control_best_median": sorted(controls)[len(controls) // 2],
        "control_best_max": max(controls),
        "all_shift_best_scores": [row["best"] for row in scores],
        "limits": "This circular-shift control conditions on the chosen sections, F handling, four operations and whole-stream IoC; it does not adjust for discovering the length equality or trying other methods."
    }


def figure(result: dict) -> str:
    lo, mid, hi = (result[key] for key in ("control_best_min", "control_best_median", "control_best_max"))
    observed = result["observed_best"]
    left, right = 35, 335
    scale = lambda x: round(left + (x - lo) * (right - left) / (hi - lo), 1)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 370 204" role="img" aria-labelledby="title desc">
<title id="title">The 1,894-rune pairing compared with circular shifts</title>
<desc id="desc">The best observed index-of-coincidence score lies within the range of shifted pairings. {result['nonzero_shifts_at_least_observed']} of {result['nonzero_shift_count']} nonzero shifts tie or exceed it.</desc>
<rect width="370" height="204" fill="#f5f6f7"/>
<text x="18" y="30" font-family="sans-serif" font-size="17" fill="#22333d">Equal length, ordinary alignment</text>
<text x="18" y="54" font-family="sans-serif" font-size="12" fill="#46555e">Best of four operations · ordered equal-rune pairs</text>
<line x1="{left}" y1="111" x2="{right}" y2="111" stroke="#65747d" stroke-width="3"/>
<circle cx="{scale(mid)}" cy="111" r="7" fill="#718b9a"/>
<line x1="{scale(observed)}" y1="83" x2="{scale(observed)}" y2="140" stroke="#1e5875" stroke-width="4"/>
<text x="{left}" y="158" font-family="sans-serif" font-size="12" fill="#46555e">shift range</text>
<text x="{right}" y="158" text-anchor="end" font-family="sans-serif" font-size="12" fill="#46555e">observed line · median dot</text>
<text x="18" y="188" font-family="sans-serif" font-size="13" fill="#22333d">{result['nonzero_shifts_at_least_observed']} of {result['nonzero_shift_count']} shifted pairings score at least as high</text>
</svg>
'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = calculate()
    json_text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    svg_text = figure(result)
    if args.write:
        (HERE / "results.json").write_text(json_text, encoding="utf-8", newline="\n")
        (HERE / "comparison.svg").write_text(svg_text, encoding="utf-8", newline="\n")
    if args.check:
        assert (HERE / "results.json").read_text(encoding="utf-8") == json_text
        assert (HERE / "comparison.svg").read_text(encoding="utf-8") == svg_text
        print("PASS: 1,894-rune pairing, four variants and all circular shifts")
    if not args.write and not args.check:
        print(json.dumps({key: result[key] for key in ("length", "variants", "observed_best", "nonzero_shifts_at_least_observed", "conditional_fraction")}, indent=2))


if __name__ == "__main__":
    main()
