"""Test a fixed list of LP2-39 header cribs under every affine key mod 29."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def report():
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    paths = ["data/index.json", "data/pages/lp2-39.json"]
    raw = {p: (ROOT / p).read_bytes() for p in paths}
    alphabet = json.loads(raw[paths[0]])["alphabet"]
    by_label = {r["latin"]: i for i, r in enumerate(alphabet)}
    by_rune = {r["rune"]: i for i, r in enumerate(alphabet)}
    line = json.loads(raw[paths[1]])["lines"][plan["line_index"]]["raw"]
    assert line.startswith(plan["prefix"])
    cipher = [by_rune[r] for r in plan["prefix"] if r in by_rune]
    assert cipher == [27, 5, 15]

    def segment(word):
        if not word:
            yield []
        for label in by_label:
            if word.startswith(label):
                for tail in segment(word[len(label):]):
                    yield [label] + tail

    rows = []
    for word in plan["candidates"]:
        variants = []
        for labels in segment(word.upper()):
            plain = [by_label[x] for x in labels]
            keys = []
            if len(plain) == len(cipher):
                for a in plan["a"]:
                    for b in plan["b"]:
                        if [(a*p+b) % 29 for p in plain] == cipher:
                            keys.append({"a": a, "b": b})
            variants.append({"labels": labels, "indices": plain, "length": len(plain),
                             "sum": sum(alphabet[i]["prime"] for i in plain),
                             "length_matches": len(plain) == len(cipher), "affine_keys": keys})
        rows.append({"word": word, "variants": variants})
    eligible = sum(v["length_matches"] for r in rows for v in r["variants"])
    return {"scope": plan, "input_sha256": {p: hashlib.sha256(b).hexdigest() for p,b in raw.items()},
            "ciphertext_indices": cipher, "candidate_count": len(rows),
            "segmentation_count": sum(len(r["variants"]) for r in rows),
            "eligible_segmentations": eligible, "affine_key_trials": eligible * 28 * 29,
            "matching_candidates": [r["word"] for r in rows if any(v["affine_keys"] for v in r["variants"])],
            "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report()
    if args.check:
        assert result == json.loads((HERE / "results.json").read_text(encoding="utf-8"))
        print("PASS: all fixed cribs, segmentations and affine keys reproduced")
    else:
        print(json.dumps(result, ensure_ascii=True, indent=2))
