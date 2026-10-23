"""Replay the reproducible R20-N2 diagonal bound from pinned rune input.

This deliberately does not claim to reproduce the missing Pride & Prejudice
control corpus. Its planted control uses an explicitly synthetic lumpy source.
"""
from __future__ import annotations

import json
import math
import random
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
INDEX = {r: i for i, r in enumerate(RUNES)}
N = 29


def runs_from_source(raw: str) -> list[list[int]]:
    runs = []
    for page in raw.split("%")[:55]:
        current = []
        pending = "start"
        for ch in page:
            if ch in INDEX:
                if pending is not None and current:
                    runs.append(current)
                    current = []
                current.append(INDEX[ch])
                pending = None
            elif ch in "\n/":
                if pending in (None, "start"):
                    pending = "line"
            elif ch == "-":
                pending = "word"
            elif ch == ".":
                pending = "sent"
        if current:
            runs.append(current)
    return runs


def diagonal_counts(runs):
    return Counter((b-a) % N for run in runs for a, b in zip(run, run[1:]))


def stats(counts):
    vals = [counts.get(i, 0) for i in range(1, N)]
    mean = sum(vals) / 28
    chi = sum((v-mean)**2 / mean for v in vals)
    cv = math.sqrt(sum((v-mean)**2 for v in vals) / 28) / mean
    return {"cv": cv, "chi": chi, "nonzero_counts": vals, "d0": counts[0]}


def max_cv_after_k(counts, k):
    """Exact max over all ways of adding k nonnegative counts to d=1..28.

    Sum of squares is convex. Transferring an increment from a smaller final
    cell to a larger one never reduces it; a maximum puts all k in an
    initially maximal cell. The common mean depends only on k.
    """
    vals = [counts.get(i, 0) for i in range(1, N)]
    j = max(range(28), key=lambda x: vals[x])
    vals[j] += k
    mean = sum(vals)/28
    return math.sqrt(sum((v-mean)**2 for v in vals)/28)/mean, j+1


def merge_first_doublets(runs, limit):
    result = [r[:] for r in runs]
    taken = 0
    for run in result:
        j = 1
        while j < len(run) and taken < limit:
            if run[j] == run[j-1]:
                del run[j]
                taken += 1
            else:
                j += 1
        if taken >= limit:
            break
    return result, taken


def synthetic_control(lengths):
    rng = random.Random(3301)
    # Deliberately lumpy, predeclared 29-symbol weights; no external corpus.
    weights = [30, 24, 20, 16, 13, 11, 9, 7, 6, 5, 4, 3] + [1]*17
    autokey = []
    uniform = []
    for length in lengths:
        plain = rng.choices(range(N), weights=weights, k=length)
        if not plain:
            continue
        c = [plain[0]]
        for p in plain[1:]:
            c.append((p + c[-1]) % N)
        autokey.append(c)
        uniform.append([rng.randrange(N) for _ in range(length)])
    a_before = stats(diagonal_counts(autokey))["cv"]
    u_before = stats(diagonal_counts(uniform))["cv"]
    a_merged, a_n = merge_first_doublets(autokey, 20)
    u_merged, u_n = merge_first_doublets(uniform, 20)
    a_after = stats(diagonal_counts(a_merged))["cv"]
    u_after = stats(diagonal_counts(u_merged))["cv"]
    return {"weights": weights, "autokey_before": a_before,
            "autokey_after_20": a_after, "uniform_before": u_before,
            "uniform_after_20": u_after, "autokey_merges": a_n,
            "uniform_merges": u_n, "separation_after": a_after-u_after}


def main():
    raw = (HERE/"source"/"krisyotam_runes.txt").read_text(encoding="utf-8")
    runs = runs_from_source(raw)
    counts = diagonal_counts(runs)
    baseline = stats(counts)
    adjacent = sum(counts.values())
    assert adjacent == 9640 and counts[0] == 60, (adjacent, counts[0])
    assert abs(baseline["cv"] - 0.0608) < .0001
    sweep = []
    for k in range(41):
        upper, d = max_cv_after_k(counts, k)
        sweep.append({"k": k, "physical_cv": baseline["cv"],
                      "free_diagonal_upper_cv": upper, "maximizing_diagonal": d})
    control = synthetic_control([len(r) for r in runs])
    assert control["autokey_merges"] == control["uniform_merges"] == 20
    assert control["autokey_before"] >= .4 and control["autokey_after_20"] >= .3
    assert control["uniform_after_20"] < .15 and control["separation_after"] >= .15
    assert baseline["cv"] == stats(Counter({**counts, 0: counts[0]+20}))["cv"]
    result = {"source": "R20-N2 pinned f08b20b", "pages": 55,
              "runs": len(runs), "adjacent_pairs": adjacent,
              "d0_doublets": counts[0], "baseline": baseline,
              "sweep": sweep, "synthetic_control": control,
              "source_comparison": {"adjacent_pairs":9640,"d0_doublets":60,
                  "cv_at_0":.0608,"free_diagonal_cv_at_20":.0656,
                  "free_diagonal_cv_at_40":.0717},
              "qualification": "Exact source English corpus is absent; control uses declared synthetic weights. Physical invariance and source bound are independently checked."}
    (HERE/"results.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(f"{adjacent} adjacent pairs, {counts[0]} doublets; cv={baseline['cv']:.6f}")
    print(f"20 physical duplicates: unchanged; 20 free-diagonal additions: cv<={sweep[20]['free_diagonal_upper_cv']:.6f}")
    print(f"synthetic planted control: autokey={control['autokey_after_20']:.3f}, uniform={control['uniform_after_20']:.3f}")


if __name__ == "__main__":
    main()
