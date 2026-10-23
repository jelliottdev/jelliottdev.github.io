"""Independent row-count entropy check of the pinned source and diagnostic."""
import ast
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row_entropy(seq, order):
    rows = defaultdict(Counter)
    for i in range(order, len(seq)):
        rows[tuple(seq[i-order:i])][seq[i]] += 1
    n = len(seq) - order
    return sum(-v * math.log2(v / sum(row.values()))
               for row in rows.values() for v in row.values()) / n


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads((HERE / "diagnostic-plan.json").read_text(encoding="utf-8"))
    source = args.source_root.resolve() / "liber-primus"
    gp = source / "src/lp/gematria.py"
    transcription = source / "data/krisyotam_runes.txt"
    assert sha(gp) == plan["alphabet_sha256"]
    assert sha(transcription) == plan["transcription_sha256"]
    module = ast.parse(gp.read_text(encoding="utf-8"))
    table = next(ast.literal_eval(node.value) for node in module.body
                 if isinstance(node, ast.Assign) and
                 any(isinstance(t, ast.Name) and t.id == "GEMATRIA" for t in node.targets))
    mapping = {rune: index for index, rune, _, _ in table}
    chunks = transcription.read_text(encoding="utf-8").split("%")
    assert len(chunks) == 57
    seq = [mapping[c] for chunk in chunks[:55] for c in chunk if c in mapping]
    assert len(seq) == 12956
    result = json.loads((HERE / "diagnostic-results.json").read_text(encoding="utf-8"))
    source_result = json.loads((HERE / "source-mdl_result.json").read_text(encoding="utf-8"))
    replay = json.loads((HERE / "replayed-mdl_result.json").read_text(encoding="utf-8"))
    assert source_result == replay
    assert result["plan_sha256"] == sha(HERE / "diagnostic-plan.json")
    assert sum(a == b for a, b in zip(seq, seq[1:])) == 86
    for order in (0, 1, 2):
        name = f"order{order}"
        own = row_entropy(seq, order)
        assert abs(own - result["real"][name]) < 1e-11
        assert abs(own - source_result["entropy_rate"][str(order)]["real"]) < 0.00006
    # A second implementation of the frozen control construction. The saved
    # 1,000 rows are checked in full; this does not import the producer.
    rng = random.Random(plan["seed"])
    assert len(result["controls"]) == plan["replicates"] == 1000
    for saved in result["controls"]:
        marks = set(rng.sample(range(1, len(seq)), 86))
        trial = [rng.randrange(29)]
        for i in range(1, len(seq)):
            previous = trial[-1]
            if i in marks:
                trial.append(previous)
            else:
                candidate = rng.randrange(28)
                trial.append(candidate + int(candidate >= previous))
        assert sum(a == b for a, b in zip(trial, trial[1:])) == 86
        for order in (0, 1, 2):
            assert abs(row_entropy(trial, order) - saved[f"order{order}"]) < 1e-11
    for key in ("order0", "order1", "order2"):
        vals = [row[key] for row in result["controls"]]
        summary = result["summaries"][key]
        assert summary["control_at_or_below_observed"] == sum(v <= result["real"][key] for v in vals)
        assert abs(summary["control_mean"] - sum(vals)/len(vals)) < 1e-12
    print("PASS: exact source replay, independent real and 1,000-control entropy rows, ranks")


if __name__ == "__main__":
    main()
