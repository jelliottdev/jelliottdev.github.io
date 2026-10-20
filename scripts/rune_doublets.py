"""Audit overlapping equal-rune pairs in LP2-00--55, with exact source locations."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "exports/unsolved-doublets.json"


def summary(streams, alphabet):
    counts = Counter()
    occurrences = []
    expectation = Fraction(0)
    windows = 0
    for stream in streams:
        frequencies = Counter(p["rune"] for p in stream)
        n = len(stream)
        windows += max(0, n-1)
        if n:
            expectation += Fraction(sum(f*(f-1) for f in frequencies.values()), n)
        for left, right in zip(stream, stream[1:]):
            if left["rune"] == right["rune"]:
                counts[left["rune"]] += 1
                occurrences.append({"left": left, "right": right})
    vector = [counts[a["rune"]] for a in alphabet]
    starts = [i for i in range(len(vector)-2) if vector[i:i+3] == [4, 2, 1]]
    return {
        "runes": sum(map(len, streams)), "windows": windows,
        "doublets": len(occurrences),
        "rate": str(Fraction(len(occurrences), windows)) if windows else None,
        "shuffle_expected_doublets": str(expectation),
        "shuffle_expected_doublets_decimal": float(expectation),
        "count_vector": vector,
        "421_start_indices_zero_based": starts,
        "occurrences": occurrences,
    }


def report():
    index_bytes = (ROOT/"data/index.json").read_bytes()
    alphabet = json.loads(index_bytes)["alphabet"]
    lookup = {a["rune"] for a in alphabet}
    assert len(lookup) == 29
    inputs = {"data/index.json": hashlib.sha256(index_bytes).hexdigest()}
    streams = []
    for number in range(56):
        page = f"lp2-{number:02d}"
        path = f"text/{page}.txt"
        data = (ROOT/path).read_bytes()
        text = data.decode("utf-8")
        unknown = {c for c in text if "\u16a0" <= c <= "\u16ff"} - lookup
        if unknown:
            raise ValueError(f"Unknown rune in {page}: {ascii(unknown)}")
        inputs[path] = hashlib.sha256(data).hexdigest()
        stream = []
        line, column = 1, 1
        for offset, ch in enumerate(text):
            if ch in lookup:
                stream.append({"rune": ch, "page": page, "rune_index_zero_based": len(stream),
                               "source_offset_zero_based": offset, "line_one_based": line,
                               "column_one_based": column})
            if ch == "\n":
                line, column = line+1, 1
            else:
                column += 1
        streams.append(stream)
    return {
        "scope": "LP2-00--55, headings included; retain only alphabet runes; overlapping windows.",
        "boundary_modes": {
            "page": "Never pair across pages; within-page non-runes are removed.",
            "joined": "Concatenate all filtered pages in numerical order, including across empty pages."},
        "expectation": "Uniform random permutations preserving each stream's rune counts. Sum f*(f-1)/N per nonempty stream. This is an expectation, not a p-value.",
        "input_sha256": inputs,
        "alphabet": [{"rune": a["rune"], "latin": a["latin"]} for a in alphabet],
        "page": summary(streams, alphabet),
        "joined": summary([sum(streams, [])], alphabet),
    }


def figure(result):
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="360" height="640" viewBox="0 0 360 640" role="img" aria-labelledby="title desc">',
             '<title id="title">Doublets by rune in LP2-00 through LP2-55</title>',
             '<desc id="desc">Counts in alphabet order. O R C, J EO P and OE D A each have counts four, two, one. Total 86; headings included, no pairs across pages.</desc>',
             '<rect width="360" height="640" fill="white"/>',
             '<g font-family="sans-serif" fill="#25343b">',
             '<text x="16" y="23" font-size="16">Equal adjacent rune pairs: 86</text>']
    highlighted = {i+j for i in result["page"]["421_start_indices_zero_based"] for j in range(3)}
    for i, (rune, count) in enumerate(zip(result["alphabet"], result["page"]["count_vector"])):
        y = 44+19*i
        color = "#30667b" if i in highlighted else "#829397"
        parts += [f'<text x="16" y="{y+12}" font-size="12">{rune["latin"]}</text>',
                  f'<rect x="53" y="{y}" width="{count*34}" height="14" fill="{color}"/>',
                  f'<text x="{61+count*34}" y="{y+12}" font-size="12">{count}</text>']
    parts += ['<text x="16" y="610" font-size="12">Blue marks the three 4–2–1 groups.</text>',
              '<text x="16" y="630" font-size="12">Observed counts; no significance claim.</text></g></svg>']
    return "\n".join(parts)+"\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report()
    chart = ROOT/"exports/figures/doublets.svg"
    if args.write:
        OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n",
                          encoding="utf-8", newline="\n")
        chart.write_text(figure(result), encoding="utf-8", newline="\n")
    if args.check:
        assert result == json.loads(OUTPUT.read_text(encoding="utf-8"))
        assert figure(result) == chart.read_text(encoding="utf-8")
        print("PASS exact counts, positions, expectations and chart")
    for mode in ("page", "joined"):
        r = result[mode]
        print(mode, r["doublets"], "/", r["windows"],
              "shuffle expectation", r["shuffle_expected_doublets_decimal"])


if __name__ == "__main__":
    main()
