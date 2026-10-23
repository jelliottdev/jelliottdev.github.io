"""Post-target matched shuffle power diagnostic for the known-text controls."""

import argparse
import hashlib
import json
import random
import subprocess
from pathlib import Path

import control
from control import RUNES, original_classes

HERE = Path(__file__).resolve().parent
BASE = json.loads((HERE / "plan.json").read_text(encoding="utf8"))
PLAN = json.loads((HERE / "shuffle-plan.json").read_text(encoding="utf8"))
ORIGINAL = json.loads((HERE / "control-results.json").read_text(encoding="utf8"))


def produce(source):
    control.SOURCE = source
    assert hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest() == PLAN["source_plan_sha256"]
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source).decode().strip() == BASE["source_revision"]
    raw = subprocess.check_output(["git", "show", "HEAD:_solved.txt"], cwd=source)
    assert hashlib.sha256(raw).hexdigest() == BASE["source_sha256"]["_solved.txt"]
    known = [RUNES.index(x) for x in raw.decode("utf8") if x in RUNES][:600]
    Pattern, Probability = original_classes(ORIGINAL["source_target_ioc"])
    rows = []
    for arm in ORIGINAL["rows"]:
        family, kind = arm["family"], arm["kind"]
        if family == "mirror":
            variant = arm["variant"]
            gen = Pattern.mirror_pattern_a(5) if variant == "a" else Pattern.mirror_pattern_b(5)
            clock = [next(gen) for _ in known]
            cipher = [(value + ((7 * clock[i] + 3) % 29)) % 29 for i, value in enumerate(known)]
            skips = set()

            def source_score(stream, k):
                generator = Pattern.mirror_pattern_a(k) if variant == "a" else Pattern.mirror_pattern_b(k)
                groups = Pattern.groups(stream, k, generator)
                return Probability.parts_high(groups, k) if kind == "high" else Probability.parts_norm(groups, k)

            def selected(stream):
                return stream

        else:
            modulus, subgroup = arm["modulus"], arm["subgroup"]
            cipher = []
            counters = [0] * modulus
            plain_pointer = 0
            skips = set(range(37, 625, 37))
            while plain_pointer < len(known):
                pos = len(cipher)
                if pos in skips:
                    cipher.append(0)
                    continue
                group = plain_pointer % modulus if family == "modulo_a" else pos % modulus
                key = (7 * ((counters[group] + group) % 5) + 3) % 29
                cipher.append((known[plain_pointer] + key) % 29)
                counters[group] += 1
                plain_pointer += 1

            def source_score(stream, k):
                return Probability.IC_w_keylen(stream, k) if kind == "high" else Probability.target_diff(stream, k)

            if family == "modulo_a":
                def selected(stream):
                    return [x for i, x in enumerate(stream) if i not in skips][subgroup::modulus]
            else:
                def selected(stream):
                    return [x for i, x in enumerate(stream) if i % modulus == subgroup and i not in skips]

        observed = source_score(selected(cipher), 5)
        assert abs(observed - arm["scores"]["5"]) < 1e-12
        maxima = []
        movable = [i for i in range(len(cipher)) if i not in skips]
        for trial in range(PLAN["replicates"]):
            shuffled = cipher[:]
            values = [cipher[i] for i in movable]
            random.Random(PLAN["seed"] + trial).shuffle(values)
            for i, value in zip(movable, values):
                shuffled[i] = value
            view = selected(shuffled)
            maxima.append(max(source_score(view, k) for k in range(2, 9)))
        rows.append({"family": family, "variant": arm.get("variant"), "modulus": arm.get("modulus"),
                     "subgroup": arm.get("subgroup"), "kind": kind, "observed_period5": observed,
                     "null_maxima": maxima, "null_max_at_least_observed": sum(v >= observed for v in maxima)})
    return {"schema": "relikd-interrupt-pattern-shuffle-results-v1", "plan_sha256": hashlib.sha256((HERE / "shuffle-plan.json").read_bytes()).hexdigest(),
            "source_control_sha256": hashlib.sha256((HERE / "control-results.json").read_bytes()).hexdigest(),
            "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = produce(args.source_root.resolve())
    path = HERE / "shuffle-results.json"
    if args.check:
        assert output == json.loads(path.read_text(encoding="utf8"))
    else:
        path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf8", newline="\n")
    print("arms", len(output["rows"]), "all-49 outrun", sum(r["null_max_at_least_observed"] == 0 for r in output["rows"]))
