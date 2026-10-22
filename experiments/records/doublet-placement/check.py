"""Independent ledger, page-length and hypergeometric checks for placement."""
from collections import Counter
import json
import math
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
old = json.loads((ROOT / "exports/unsolved-doublets.json").read_text(encoding="utf-8"))["page"]["occurrences"]
alphabet = {entry["rune"] for entry in json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]}
event_positions = []
page_counts = Counter()
global_start = 0
edge_counts = []
for number in range(56):
    page = f"lp2-{number:02d}"
    text = (ROOT / f"text/{page}.txt").read_text(encoding="utf-8")
    runes = [match.group() for match in re.finditer(r"[\u16a0-\u16ff]", text)]
    assert all(rune in alphabet for rune in runes)
    indices = [i for i, (a, b) in enumerate(zip(runes, runes[1:])) if a == b]
    page_counts[page] = len(indices)
    edge_counts.append(max(0, len(runes)-1))
    event_positions.extend(global_start + i for i in indices)
    stored = result["pages"][number]
    assert (stored["page"], stored["runes"], stored["edges"], stored["event_edge_indices"]) == (
        page, len(runes), max(0, len(runes)-1), indices)
    global_start += len(runes)
assert len(event_positions) == len(old) == 86
assert [entry["global_rune_index_zero_based"] for entry in result["event_slots"]] == event_positions
assert [(entry["page"], entry["edge_index_zero_based"]) for entry in result["event_slots"]] == [
    (item["left"]["page"], item["left"]["rune_index_zero_based"]) for item in old]
nonempty = [f"lp2-{i:02d}" for i, edges in enumerate(edge_counts) if edges]
vector = [page_counts[page] for page in nonempty]
gaps = [b-a for a, b in zip(event_positions, event_positions[1:])]
observed = result["observed"]
assert observed["zero_pages"] == vector.count(0) == 13
assert abs(observed["page_variance_to_mean"] - statistics.pvariance(vector)/statistics.mean(vector)) < 1e-15
assert observed["minimum_rune_gap"] == min(gaps) == 6
assert observed["median_rune_gap"] == statistics.median(gaps) == 113
assert observed["gaps_at_most_five"] == sum(gap <= 5 for gap in gaps) == 0
assert (observed["first_five_edges"], observed["last_five_edges"]) == (
    sum(item["edge_index_zero_based"] < 5 for item in result["event_slots"]),
    sum(item["edge_index_zero_based"] >= edge_counts[int(item["page"][-2:])]-5
        for item in result["event_slots"]))
N = sum(edge_counts)
expected_zeros = sum(math.comb(N-edges, 86) / math.comb(N, 86)
                     for edges in edge_counts if edges)
assert N == 12901
assert abs(expected_zeros-result["total_only_null"]["exact_expected_zero_pages"]) < 1e-10
print("PASS independent event positions, page metrics and exact zero-page expectation")
