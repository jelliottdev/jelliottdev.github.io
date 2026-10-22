"""Compare LP2-00--55 equality at rune lags 1--5 with page-wise shuffles."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
REPETITIONS = 2000
SEED = 330155
LAGS = range(1, 6)


def count_lags(streams):
    rows = []
    for lag in LAGS:
        pairs = sum(max(0, len(stream) - lag) for stream in streams)
        matches = sum(sum(a == b for a, b in zip(stream, stream[lag:])) for stream in streams)
        rows.append({"lag": lag, "matches": matches, "pairs": pairs,
                     "rate": matches / pairs})
    return rows


def quantile(sorted_values, p):
    # Nearest-rank quantile; this convention is stored with the output.
    return sorted_values[max(0, min(len(sorted_values) - 1, int(p * len(sorted_values) + .999999) - 1))]


def report():
    raw_index = (ROOT / "data/index.json").read_bytes()
    index = json.loads(raw_index)
    alphabet = [entry["rune"] for entry in index["alphabet"]]
    assert len(set(alphabet)) == 29
    lookup = {rune: i for i, rune in enumerate(alphabet)}
    hashes = {"data/index.json": hashlib.sha256(raw_index).hexdigest()}
    streams = []
    for number in range(56):
        name = f"text/lp2-{number:02d}.txt"
        raw = (ROOT / name).read_bytes()
        text = raw.decode("utf-8")
        unknown = {c for c in text if "\u16a0" <= c <= "\u16ff"} - lookup.keys()
        if unknown:
            raise ValueError(f"Unmapped rune in {name}: {unknown!r}")
        stream = [lookup[c] for c in text if c in lookup]
        expected = next(page["rune_count"] for page in index["pages"]
                        if page["id"] == f"lp2-{number:02d}")
        assert len(stream) == expected, name
        streams.append(stream)
        hashes[name] = hashlib.sha256(raw).hexdigest()
    observed = count_lags(streams)
    expected_rate_numerators = []
    for stream in streams:
        n = len(stream)
        counts = Counter(stream)
        expected_rate_numerators.append(
            Fraction(sum(c * (c - 1) for c in counts.values()), n * (n - 1))
            if n > 1 else Fraction(0))
    rng = random.Random(SEED)
    shuffled = [[] for _ in LAGS]
    for _ in range(REPETITIONS):
        trial = [stream.copy() for stream in streams]
        for stream in trial:
            rng.shuffle(stream)
        for i, row in enumerate(count_lags(trial)):
            shuffled[i].append(row["matches"])
    for i, row in enumerate(observed):
        lag = row["lag"]
        expected = sum(max(0, len(stream) - lag) * rate
                       for stream, rate in zip(streams, expected_rate_numerators))
        values = sorted(shuffled[i])
        row["shuffle_expected_fraction"] = str(expected)
        row["shuffle_expected"] = float(expected)
        row["shuffle_95pct_interval"] = [quantile(values, .025), quantile(values, .975)]
        row["shuffle_min_max"] = [values[0], values[-1]]
        row["shuffles_at_most_observed"] = sum(v <= row["matches"] for v in values)
        row["shuffles_at_least_observed"] = sum(v >= row["matches"] for v in values)
    return {
        "schema": "liberpedia-doublet-lag-profile-v1", "input_sha256": hashes,
        "scope": "LP2-00--55, alphabet runes and headings retained; non-runes removed within pages; no cross-page pairs or circular wrap.",
        "rune_count": sum(map(len, streams)), "nonempty_pages": sum(bool(s) for s in streams),
        "shuffle": {"model": "Uniformly shuffle each page's filtered runes, preserving each page's symbol counts and length.",
                    "repetitions": REPETITIONS, "seed": SEED,
                    "quantile": "Nearest rank: sorted value at ceil(p*N), one-based.",
                    "tail_note": "Monte Carlo counts are descriptive; 0/2000 does not imply zero probability. Lags were examined after lag-one suppression was known."},
        "rows": observed,
    }


def figure(result):
    rows = result["rows"]
    width, height = 640, 320
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
             '<title id="title">Equal rune pairs by lag across LP2-00 through LP2-55</title>',
             '<desc id="desc">Lag one has 86 matches, far below the page-shuffle range. Lags two through five are close to the page-shuffle expectation. Intervals are empirical, not cipher-model confidence bounds.</desc>',
             '<rect width="640" height="320" fill="white"/>',
             '<g font-family="system-ui, sans-serif" fill="#263842">',
             '<text x="20" y="29" font-size="19">Equal rune pairs by distance</text>',
             '<text x="20" y="51" font-size="12">LP2-00–55 · within pages · fixed-count page shuffles</text>']
    for i, row in enumerate(rows):
        y = 83 + 46 * i
        x0, x1 = 126, 555
        scale = (x1 - x0) / 500
        lo, hi = row["shuffle_95pct_interval"]
        ex = row["shuffle_expected"]
        obs = row["matches"]
        parts += [f'<text x="20" y="{y+5}" font-size="14">Lag {row["lag"]}</text>',
                  f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="#e4e8e7" stroke-width="2"/>',
                  f'<rect x="{x0+lo*scale:.1f}" y="{y-8}" width="{(hi-lo)*scale:.1f}" height="16" fill="#c4d4d1"/>',
                  f'<line x1="{x0+ex*scale:.1f}" y1="{y-11}" x2="{x0+ex*scale:.1f}" y2="{y+11}" stroke="#607d7a" stroke-width="2"/>',
                  f'<circle cx="{x0+obs*scale:.1f}" cy="{y}" r="6" fill="#245d74"/>',
                  f'<text x="{x1+12}" y="{y+5}" font-size="13">{obs}</text>']
    parts += ['<text x="126" y="305" font-size="12">0</text>',
              '<text x="516" y="305" font-size="12">500 matches</text>',
              '</g></svg>']
    return "\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report()
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    svg = figure(result)
    if args.write:
        (HERE / "results.json").write_text(payload, encoding="utf-8", newline="\n")
        (HERE / "profile.svg").write_text(svg, encoding="utf-8", newline="\n")
    if args.check:
        assert payload == (HERE / "results.json").read_text(encoding="utf-8")
        assert svg == (HERE / "profile.svg").read_text(encoding="utf-8")
        print("PASS lag counts, page-shuffle controls and figure")
    for row in result["rows"]:
        print(row["lag"], row["matches"], "/", row["pairs"],
              "expected", round(row["shuffle_expected"], 2),
              "interval", row["shuffle_95pct_interval"])


if __name__ == "__main__":
    main()
