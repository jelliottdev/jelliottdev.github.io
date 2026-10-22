"""Bounded search for LP2-39 crib-derived difference strings in other LP pages."""
import argparse
import collections
import hashlib
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def segment(word, labels):
    if not word:
        yield ()
    for label in labels:
        if word.startswith(label):
            for tail in segment(word[len(label):], labels):
                yield (label,) + tail


def prepare():
    plan = read("experiments/records/crib-difference-stream-search/plan.json")
    crib_plan = read(plan["crib_source"])
    alphabet = read("data/index.json")["alphabet"]
    rune_to_index = {row["rune"]: i for i, row in enumerate(alphabet)}
    label_to_index = {row["latin"]: i for i, row in enumerate(alphabet)}
    target = read(f'data/pages/{plan["target_page"]}.json')
    line = target["lines"][plan["target_line_index"]]["raw"]
    assert line.startswith(plan["target_prefix"])
    cipher = tuple(rune_to_index[c] for c in plan["target_prefix"] if c in rune_to_index)
    assert len(cipher) == 3
    candidates = []
    for word in crib_plan["candidates"]:
        for labels in segment(word.upper(), label_to_index):
            if len(labels) != 3:
                continue
            plain = tuple(label_to_index[x] for x in labels)
            diff = tuple((c - p) % 29 for c, p in zip(cipher, plain))
            candidates.append({"word": word, "labels": list(labels), "plaintext_indices": list(plain), "difference_indices": list(diff)})
    seq_to_cribs = collections.defaultdict(list)
    for c in candidates:
        seq_to_cribs[tuple(c["difference_indices"])].append(c["word"] + " [" + ",".join(c["labels"]) + "]")
    source = []
    files = []
    for path in sorted((ROOT / "data/pages").glob("lp[12]-*.json")):
        if path.stem == plan["target_page"]:
            continue
        page = json.loads(path.read_text(encoding="utf-8"))
        if not page["rune_count"]:
            continue
        stream = tuple(rune_to_index[c] for c in page["raw"] if c in rune_to_index)
        assert len(stream) == page["rune_count"], path
        source.append((path.stem, stream))
        files.append(path.relative_to(ROOT).as_posix())
    return plan, cipher, candidates, seq_to_cribs, source, files, alphabet


def hits(source, seq_to_cribs):
    wanted = set(seq_to_cribs)
    found = []
    for page, seq in source:
        for offset in range(len(seq) - 2):
            tri = seq[offset:offset + 3]
            if tri in wanted:
                found.append({"page": page, "rune_offset_0": offset,
                              "difference_indices": list(tri), "cribs": seq_to_cribs[tri]})
    return found


def report():
    plan, cipher, candidates, seq_to_cribs, source, files, alphabet = prepare()
    actual = hits(source, seq_to_cribs)
    seen = {tuple(h["difference_indices"]) for h in actual}
    rng = random.Random(330139)
    control = []
    for _ in range(2000):
        shuffled = []
        for name, values in source:
            values = list(values)
            rng.shuffle(values)
            shuffled.append((name, tuple(values)))
        control.append(len(hits(shuffled, seq_to_cribs)))
    positives = list(source)
    name, values = positives[0]
    first = next(iter(seq_to_cribs))
    positives[0] = (name, tuple(first) + values[3:])
    assert any(h["page"] == name and h["rune_offset_0"] == 0 and
               tuple(h["difference_indices"]) == first for h in hits(positives, seq_to_cribs))
    observed = len(actual)
    hist = dict(sorted(collections.Counter(control).items()))
    plan_path = "experiments/records/crib-difference-stream-search/plan.json"
    paths = [plan_path, "data/index.json", plan["crib_source"], f'data/pages/{plan["target_page"]}.json'] + files
    return {
        "plan": plan,
        "plan_sha256": hashlib.sha256((ROOT / plan_path).read_bytes()).hexdigest(),
        "input_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        "ciphertext_indices": list(cipher),
        "source_page_count": len(source),
        "source_rune_count": sum(len(s) for _, s in source),
        "eligible_crib_segmentations": len(candidates),
        "distinct_difference_sequences": len(seq_to_cribs),
        "cribs": candidates,
        "observed_matching_windows": observed,
        "distinct_sequences_with_hits": len(seen),
        "hits": actual,
        "control": {
            "replicates": len(control), "seed": 330139,
            "mean_matching_windows": sum(control) / len(control),
            "histogram": {str(k): v for k, v in hist.items()},
            "at_least_observed": sum(v >= observed for v in control),
            "at_most_observed": sum(v <= observed for v in control),
            "p_upper_plus_one": (1 + sum(v >= observed for v in control)) / (len(control) + 1),
            "p_lower_plus_one": (1 + sum(v <= observed for v in control)) / (len(control) + 1)
        },
        "positive_control": {"page": name, "rune_offset_0": 0, "difference_indices": list(first), "recovered": True}
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = (json.dumps(report(), ensure_ascii=True, indent=2) + "\n").encode("utf-8")
    output = HERE / "results.json"
    if args.check:
        assert output.read_bytes() == data
        print("PASS: crib sequences, all hits and 2,000 shuffles reproduced")
    else:
        output.write_bytes(data)
        print(output)
