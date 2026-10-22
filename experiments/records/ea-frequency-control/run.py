"""Compare EA in solved GP readings with LP2 doublets and parsing controls."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BOOTSTRAPS = 10000
NULL_TRIALS = 2000
BOOTSTRAP_SEED = 3301
NULL_SEED = 330156


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def percentile(values, p):
    ordered = sorted(values)
    return ordered[max(0, min(len(ordered) - 1, int(p * len(ordered) + .999999) - 1))]


def greedy(text, labels):
    order = sorted(enumerate(labels), key=lambda pair: (-len(pair[1]), pair[0]))
    result = []
    position = 0
    while position < len(text):
        match = next(((i, label) for i, label in order if text.startswith(label, position)), None)
        if match is None:
            raise ValueError(f"Cannot parse Latin label at offset {position}: {text[position:position+8]!r}")
        index, label = match
        result.append(index)
        position += len(label)
    return result


def report():
    index_bytes = (ROOT / "data/index.json").read_bytes()
    reading_bytes = (ROOT / "data/evidence/known-readings.json").read_bytes()
    index = json.loads(index_bytes)
    readings = json.loads(reading_bytes)
    labels = [entry["latin"] for entry in index["alphabet"]]
    rune_to_index = {entry["rune"]: i for i, entry in enumerate(index["alphabet"])}
    assert len(labels) == len(rune_to_index) == 29 and labels[28] == "EA"
    hashes = {"data/index.json": sha(index_bytes),
              "data/evidence/known-readings.json": sha(reading_bytes)}
    solved_pages = []
    cross_word_ea = []
    for control in readings["controls"]:
        for page in control["decoded_pages"]:
            indices = page["rune_indices"]
            literal = page["literal_transliteration"]
            letters = "".join(re.findall(r"[A-Z]+", literal))
            assert "".join(labels[i] for i in indices) == letters
            # Slash and LF are row wraps; hyphens and other punctuation retain token edges.
            tokens = re.findall(r"[A-Z]+", literal.replace("/", "").replace("\r", "").replace("\n", ""))
            word_aware = [i for token in tokens for i in greedy(token, labels)]
            assert word_aware == indices, page["page"]
            erased = greedy("".join(tokens), labels)
            boundary_merges = [{"page": page["page"], "left": left, "right": right}
                               for left, right in zip(tokens, tokens[1:])
                               if left.endswith("E") and right.startswith("A")]
            cross_word_ea.extend(boundary_merges)
            solved_pages.append({"page": page["page"], "control": control["id"],
                                 "runes": len(indices), "transition_positions": max(0, len(indices)-1),
                                 "ea_all": indices.count(28), "ea_after_first": indices[1:].count(28),
                                 "word_aware_greedy_matches_gp_indices": True,
                                 "boundary_erased_ea": erased.count(28)})
    def aggregate(rows):
        positions = sum(row["transition_positions"] for row in rows)
        events = sum(row["ea_after_first"] for row in rows)
        return {"pages": len(rows), "positions": positions, "ea_events": events,
                "rate_fraction": str(Fraction(events, positions)), "rate": events / positions}
    lp1_rows = [row for row in solved_pages if row["page"].startswith("lp1-")]
    lp2_rows = [row for row in solved_pages if row["page"].startswith("lp2-")]
    lp1 = aggregate(lp1_rows)
    lp2 = aggregate(lp2_rows)
    rng = random.Random(BOOTSTRAP_SEED)
    scaled_page_mix = []
    for _ in range(BOOTSTRAPS):
        draw = [rng.choice(lp1_rows) for _ in lp1_rows]
        rate = sum(row["ea_after_first"] for row in draw) / sum(row["transition_positions"] for row in draw)
        scaled_page_mix.append(rate)
    streams = []
    for number in range(56):
        name = f"text/lp2-{number:02d}.txt"
        raw = (ROOT / name).read_bytes()
        text = raw.decode("utf-8")
        unknown = {c for c in text if "\u16a0" <= c <= "\u16ff"} - rune_to_index.keys()
        if unknown:
            raise ValueError(f"Unknown Runic-block character in {name}: {unknown!r}")
        streams.append([rune_to_index[c] for c in text if c in rune_to_index])
        hashes[name] = sha(raw)
    differences = [(stream[i] - stream[i-1]) % 29
                   for stream in streams for i in range(1, len(stream))]
    counts = Counter(differences)
    n = len(differences)
    zeros = counts[0]
    observed_ioc = Fraction(sum(c*(c-1) for c in counts.values()), n*(n-1))
    expected_ioc = Fraction(zeros*(zeros-1), n*(n-1)) + Fraction((n-zeros)*(n-zeros-1), 28*n*(n-1))
    null_rng = random.Random(NULL_SEED)
    simulated_ioc = []
    for _ in range(NULL_TRIALS):
        nonzero_counts = [0] * 28
        for _ in range(n-zeros):
            nonzero_counts[null_rng.randrange(28)] += 1
        numerator = zeros*(zeros-1) + sum(c*(c-1) for c in nonzero_counts)
        simulated_ioc.append(numerator / (n*(n-1)))
    assert zeros == 86 and n == 12901
    assert sum(row["boundary_erased_ea"] for row in lp1_rows) - sum(row["ea_all"] for row in lp1_rows) == 11
    return {
        "schema": "liberpedia-ea-frequency-control-v1", "input_sha256": hashes,
        "scope": "Known decoded GP indices on LP1-01, 03--16 and LP2-56--57; archived unsolved LP2-00--55 rune streams including headings, within-page transitions only.",
        "solved_pages": solved_pages,
        "solved_lp1": lp1, "solved_lp2": lp2,
        "lp1_scaled_to_unsolved_length": lp1["rate"] * n,
        "lp1_page_bootstrap": {"pages_resampled": len(lp1_rows), "draws": BOOTSTRAPS,
                               "seed": BOOTSTRAP_SEED,
                               "scaled_count_2p5_50_97p5": [percentile(scaled_page_mix, p)*n for p in (.025, .5, .975)],
                               "note": "Descriptive resampling of the 15 solved LP1 pages, not a predictive confidence interval for unsolved LP2 or an independence claim about pages."},
        "latin_segmentation": {"word_aware_greedy_recovers_all_solved_gp_pages": True,
                               "lp1_actual_ea": sum(row["ea_all"] for row in lp1_rows),
                               "lp1_boundary_erased_greedy_ea": sum(row["boundary_erased_ea"] for row in lp1_rows),
                               "lp1_cross_word_ea_merges": [x for x in cross_word_ea if x["page"].startswith("lp1-")],
                               "rule": "Longest available GP Latin label first, after removing slash/CR/LF row wraps. Word-aware retains punctuation as token edges; boundary-erased removes all token edges within a page. This is a control on literal rune labels, not a rule for normalizing English spelling."},
        "unsolved_lp2": {"transition_positions": n, "equal_neighbors": zeros,
                         "rate_fraction": str(Fraction(zeros, n)), "rate": zeros/n,
                         "difference_counts": [counts[i] for i in range(29)],
                         "difference_ioc_fraction": str(observed_ioc), "difference_ioc": float(observed_ioc)},
        "nonzero_uniform_control": {"model": "Condition on exactly 86 zero differences; independently draw the other 12,815 difference values uniformly from residues 1--28. This tests residual balance, not the EA hypothesis or a decryption.",
                                    "expected_ioc_fraction": str(expected_ioc), "expected_ioc": float(expected_ioc),
                                    "trials": NULL_TRIALS, "seed": NULL_SEED,
                                    "ioc_2p5_50_97p5": [percentile(simulated_ioc, p) for p in (.025, .5, .975)],
                                    "trials_at_least_observed": sum(value >= float(observed_ioc) for value in simulated_ioc),
                                    "selection_note": "The low zero count and difference IoC were known before this control. Monte Carlo ranks are descriptive and unadjusted for selection."},
        "interpretation": "A comparable EA rate is a necessary-frequency calibration only; many unrelated mechanisms can reproduce it. The solved controls differ in section, method and length from unsolved LP2."
    }


def figure(result):
    lp1 = result["solved_lp1"]
    unsolved = result["unsolved_lp2"]
    upper = 1.15
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="640" height="260" viewBox="0 0 640 260" role="img" aria-labelledby="title desc">',
             '<title id="title">EA frequency in solved GP pages and doublets in unsolved LP2</title>',
             '<desc id="desc">Solved LP1 has 20 EA events in 2782 within-page positions, or 0.719 percent. Unsolved LP2 has 86 doublets in 12901 positions, or 0.667 percent. The rates are close but do not identify a cipher.</desc>',
             '<rect width="640" height="260" fill="white"/>',
             '<g font-family="system-ui, sans-serif" fill="#263842">',
             '<text x="20" y="30" font-size="19">EA frequency and the doublet count</text>',
             '<text x="20" y="51" font-size="12">Different corpora and measurements; the proposed rule connects them only conditionally</text>']
    for i, (label, count, total, rate, color) in enumerate([
        ("Solved LP1 · EA", lp1["ea_events"], lp1["positions"], lp1["rate"], "#285e75"),
        ("Unsolved LP2 · equal neighbors", unsolved["equal_neighbors"], unsolved["transition_positions"], unsolved["rate"], "#a36f43")]):
        y = 101 + 68*i
        parts += [f'<text x="20" y="{y}" font-size="13">{label}</text>',
                  f'<rect x="20" y="{y+10}" width="{rate*100/upper*420:.1f}" height="20" fill="{color}"/>',
                  f'<text x="451" y="{y+26}" font-size="13">{count}/{total} · {rate*100:.3f}%</text>']
    parts += ['<text x="20" y="244" font-size="11">Similarity of rates is not independent evidence for the running-sum equation.</text>',
              '</g></svg>']
    return "\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report()
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    chart = figure(result)
    if args.write:
        (HERE / "results.json").write_text(payload, encoding="utf-8", newline="\n")
        (HERE / "comparison.svg").write_text(chart, encoding="utf-8", newline="\n")
    if args.check:
        assert payload == (HERE / "results.json").read_text(encoding="utf-8")
        assert chart == (HERE / "comparison.svg").read_text(encoding="utf-8")
        print("PASS solved EA, unsolved doublets, segmentation and difference-IoC controls")
    print("LP1 EA", result["solved_lp1"], "unsolved LP2", result["unsolved_lp2"]["equal_neighbors"], "/", result["unsolved_lp2"]["transition_positions"])
    print("Boundary-erased GP EA", result["latin_segmentation"]["lp1_boundary_erased_greedy_ea"])
    print("Difference IoC", result["unsolved_lp2"]["difference_ioc"], "conditional interval", result["nonzero_uniform_control"]["ioc_2p5_50_97p5"])


if __name__ == "__main__":
    main()
