"""Audit page and position placement of the 86 LP2 doublets."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import statistics

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
TRIALS = 10000
SEED_TOTAL = 330186
SEED_PAGES = 33015586


def quantile(values, probability):
    ordered = sorted(values)
    return ordered[max(0, min(len(ordered)-1, int(probability*len(ordered)+.999999)-1))]


def metrics(selected, slots, page_count, valid_pages):
    counts = Counter(slots[i][0] for i in selected)
    vector = [counts[page] for page in valid_pages]
    positions = sorted(slots[i][2] for i in selected)
    gaps = [b-a for a, b in zip(positions, positions[1:])]
    mean = statistics.mean(vector)
    first_five = sum(slots[i][1] < 5 for i in selected)
    last_five = sum(slots[i][1] >= page_count[slots[i][0]]-5 for i in selected)
    return {
        "zero_pages": vector.count(0),
        "page_variance_to_mean": statistics.pvariance(vector)/mean,
        "first_five_edges": first_five,
        "last_five_edges": last_five,
        "first_or_last_five_edges": first_five + last_five,
        "minimum_rune_gap": min(gaps),
        "median_rune_gap": statistics.median(gaps),
        "gaps_at_most_five": sum(g <= 5 for g in gaps),
    }


def summarize(values, observed):
    return {"mean": statistics.mean(values),
            "central_95pct": [quantile(values, .025), quantile(values, .975)],
            "at_most_observed": sum(value <= observed for value in values),
            "at_least_observed": sum(value >= observed for value in values)}


def report():
    raw_index = (ROOT / "data/index.json").read_bytes()
    alphabet = {entry["rune"] for entry in json.loads(raw_index)["alphabet"]}
    assert len(alphabet) == 29
    hashes = {"data/index.json": hashlib.sha256(raw_index).hexdigest()}
    slots, event_slots, per_page = [], [], []
    global_offset = 0
    for number in range(56):
        page = f"lp2-{number:02d}"
        name = f"text/{page}.txt"
        raw = (ROOT/name).read_bytes()
        text = raw.decode("utf-8")
        unknown = {c for c in text if "\u16a0" <= c <= "\u16ff"} - alphabet
        if unknown:
            raise ValueError(f"Unknown Runic-block character in {page}: {unknown!r}")
        stream = [c for c in text if c in alphabet]
        hashes[name] = hashlib.sha256(raw).hexdigest()
        indices = []
        for edge, (left, right) in enumerate(zip(stream, stream[1:])):
            index = len(slots)
            slots.append((page, edge, global_offset+edge))
            if left == right:
                indices.append(index)
                event_slots.append(index)
        per_page.append({"page": page, "runes": len(stream), "edges": max(0, len(stream)-1),
                         "doublets": len(indices), "event_edge_indices": [slots[i][1] for i in indices]})
        global_offset += len(stream)
    valid_pages = [row["page"] for row in per_page if row["edges"]]
    edge_count = {row["page"]: row["edges"] for row in per_page}
    assert len(slots) == 12901 and len(event_slots) == 86 and len(valid_pages) == 55
    observed = metrics(event_slots, slots, edge_count, valid_pages)
    by_page = {page: [] for page in valid_pages}
    for i, (page, _, _) in enumerate(slots):
        by_page[page].append(i)
    observed_counts = {row["page"]: row["doublets"] for row in per_page}
    total_rng, page_rng = random.Random(SEED_TOTAL), random.Random(SEED_PAGES)
    total_values = {key: [] for key in observed}
    page_values = {key: [] for key in observed}
    for _ in range(TRIALS):
        total_trial = total_rng.sample(range(len(slots)), len(event_slots))
        page_trial = [index for page in valid_pages
                      for index in page_rng.sample(by_page[page], observed_counts[page])]
        for output, selected in ((total_values, total_trial), (page_values, page_trial)):
            for key, value in metrics(selected, slots, edge_count, valid_pages).items():
                output[key].append(value)
    # The zero-page expectation under total-only placement is a sum of exact
    # hypergeometric no-event probabilities, not 55 times one average length.
    no_event_probabilities = []
    for page in valid_pages:
        edges = edge_count[page]
        probability = 1.0
        for j in range(len(event_slots)):
            probability *= (len(slots)-edges-j)/(len(slots)-j)
        no_event_probabilities.append(probability)
    return {
        "schema": "liberpedia-doublet-placement-v1", "input_sha256": hashes,
        "scope": "LP2-00--55, 29 archived alphabet runes per page, headings included; within-page equal-neighbor events only. Global gaps use concatenated rune coordinates but never create a cross-page event.",
        "runes": global_offset, "available_edges": len(slots), "doublets": len(event_slots),
        "pages": per_page, "event_slots": [
            {"page": slots[i][0], "edge_index_zero_based": slots[i][1],
             "global_rune_index_zero_based": slots[i][2]} for i in event_slots],
        "observed": observed,
        "total_only_null": {"rule": "Condition on 86 events; choose 86 distinct within-page edge slots uniformly across all 12,901 slots. Page lengths remain fixed, page event counts vary.",
                            "trials": TRIALS, "seed": SEED_TOTAL,
                            "exact_expected_zero_pages": sum(no_event_probabilities),
                            "metrics": {key: summarize(values, observed[key]) for key, values in total_values.items()}},
        "page_counts_fixed_null": {"rule": "Condition on each observed page's doublet count; uniformly choose that many distinct edge slots within each page. Page-level zero count and variance-to-mean are fixed by construction.",
                                   "trials": TRIALS, "seed": SEED_PAGES,
                                   "metrics": {key: summarize(values, observed[key])
                                               for key, values in page_values.items()
                                               if key not in ("zero_pages", "page_variance_to_mean")}},
        "quantile": "Nearest rank at ceil(p*N), one-based. Ties are included in both at-most and at-least counts.",
        "limits": "Both nulls place events independently of rune identity, word structure and any cipher or language mechanism; overlapping equal-pair constraints are not simulated. Tests were designed after the 86 events were known."
    }


def figure(result):
    observed = result["observed"]
    total = result["total_only_null"]["metrics"]
    fields = [
        ("Pages with no doublet", "zero_pages", 26, 1.0),
        ("Page variance / mean", "page_variance_to_mean", 2.5, 1.0),
        ("Shortest gap, runes", "minimum_rune_gap", 18, 1.0),
        ("First or last five edges", "first_or_last_five_edges", 15, 1.0),
    ]
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="690" height="330" viewBox="0 0 690 330" role="img" aria-labelledby="title desc">',
             '<title id="title">Placement of 86 LP2 doublets against length-aware random placement</title>',
             '<desc id="desc">Observed empty pages, page count variance, shortest gap and first-or-last-five event count are compared with random placement of 86 events among within-page edges. These are conditional reference ranges, not cipher-model predictions.</desc>',
             '<rect width="690" height="330" fill="white"/>',
             '<g font-family="system-ui, sans-serif" fill="#263842">',
             '<text x="18" y="31" font-size="18">Where the 86 doublets fall</text>',
             '<text x="18" y="52" font-size="12">Fixed total; edge slots weighted by page length · 10,000 placements</text>']
    for i, (label, key, upper, _) in enumerate(fields):
        y = 96 + 57*i
        low, high = total[key]["central_95pct"]
        value = observed[key]
        scale = 260/upper
        parts += [f'<text x="18" y="{y}" font-size="13">{label}</text>',
                  f'<line x1="325" y1="{y-5}" x2="585" y2="{y-5}" stroke="#e4e8e7" stroke-width="2"/>',
                  f'<rect x="{325+low*scale:.1f}" y="{y-13}" width="{(high-low)*scale:.1f}" height="16" fill="#c3d4d0"/>',
                  f'<circle cx="{325+value*scale:.1f}" cy="{y-5}" r="6" fill="#245d74"/>',
                  f'<text x="608" y="{y}" font-size="13">{value:.2f}</text>']
    parts += ['<text x="18" y="319" font-size="11">Bands: descriptive central ranges; see article for separate edge controls and model limits.</text>',
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
        (HERE / "placement.svg").write_text(chart, encoding="utf-8", newline="\n")
    if args.check:
        assert payload == (HERE / "results.json").read_text(encoding="utf-8")
        assert chart == (HERE / "placement.svg").read_text(encoding="utf-8")
        print("PASS page counts, gaps, edge windows, simulations and figure")
    print("observed", result["observed"])
    print("total-only zero-page expectation", result["total_only_null"]["exact_expected_zero_pages"])


if __name__ == "__main__":
    main()
