"""Post-observation repeat-matched control for the source's entropy dip."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import statistics
import sys

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def entropy(counts):
    n = sum(counts.values())
    return math.log2(n) - sum(v * math.log2(v) for v in counts.values()) / n


def profile(seq):
    # H(X_i|X_(i-1)) = H(X_(i-1),X_i) - H(X_(i-1)).
    # The order-two calculation uses the analogous triple/pair difference.
    one = Counter(seq)
    two = Counter(zip(seq, seq[1:]))
    two_context = Counter(zip(seq[:-1], seq[1:-1]))
    three = Counter(zip(seq, seq[1:], seq[2:]))
    return {
        "order0": entropy(one),
        "order1": entropy(two) - entropy(Counter(seq[:-1])),
        "order2": entropy(three) - entropy(two_context),
        "equal_adjacent": sum(x == y for x, y in zip(seq, seq[1:])),
    }


def make_control(rng, n, n_repeats):
    marks = set(rng.sample(range(1, n), n_repeats))
    seq = [rng.randrange(29)]
    for i in range(1, n):
        prev = seq[-1]
        if i in marks:
            seq.append(prev)
        else:
            draw = rng.randrange(28)
            seq.append(draw + (draw >= prev))
    return seq


def source_sequence(source_root, plan):
    root = source_root / "liber-primus"
    gp_path = root / "src/lp/gematria.py"
    text_path = root / "data/krisyotam_runes.txt"
    if sha(gp_path) != plan["alphabet_sha256"] or sha(text_path) != plan["transcription_sha256"]:
        raise ValueError("Pinned source input differs")
    spec = importlib.util.spec_from_file_location("pinned_gp", gp_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    segments = text_path.read_text(encoding="utf-8").split("%")
    assert len(segments) == 57
    seq = [mod.RUNE_TO_IDX[c] for segment in segments[:55] for c in segment if c in mod.RUNE_TO_IDX]
    assert len(seq) == 12956
    return seq


def summary(values, observed):
    arr = sorted(values)
    n = len(arr)
    mu = statistics.mean(arr)
    sd = statistics.stdev(arr)
    return {
        "observed": observed,
        "control_mean": mu,
        "control_sd": sd,
        "control_central95": [arr[int(0.025 * n)], arr[int(0.975 * n) - 1]],
        "control_at_or_below_observed": sum(x <= observed for x in values),
        "control_count": n,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    plan = json.loads((HERE / "diagnostic-plan.json").read_text(encoding="utf-8"))
    seq = source_sequence(args.source_root.resolve(), plan)
    real = profile(seq)
    assert real["equal_adjacent"] == 86
    rng = random.Random(plan["seed"])
    controls = [profile(make_control(rng, len(seq), real["equal_adjacent"]))
                for _ in range(plan["replicates"])]
    assert all(c["equal_adjacent"] == 86 for c in controls)
    result = {
        "schema": "dukotah-mdl-repeat-matched-diagnostic-results-v1",
        "plan_sha256": sha(HERE / "diagnostic-plan.json"),
        "real": real,
        "summaries": {key: summary([c[key] for c in controls], real[key])
                      for key in ("order0", "order1", "order2")},
        "controls": controls,
    }
    target = HERE / "diagnostic-results.json"
    if args.check:
        previous = json.loads(target.read_text(encoding="utf-8"))
        assert result == previous
        print("PASS: all 1,000 repeat-matched controls and entropy summaries reproduce")
    else:
        target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(result["summaries"], indent=2))


if __name__ == "__main__":
    main()
