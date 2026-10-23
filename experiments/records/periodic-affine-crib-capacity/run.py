"""Count periodic invertible-affine keys compatible with fixed twelve-rune cribs."""
import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
INPUTS = {item["path"]: item["sha256"] for item in PLAN["inputs"]}


def source(path):
    relative = path.relative_to(ROOT).as_posix()
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != INPUTS[relative]:
        raise ValueError(f"Changed input: {relative}")
    return raw


def compatible(cipher, proposed, period, modulus):
    """Factor full-key choices into independent (multiplier, offset) slots."""
    allowed = []
    for slot in range(period):
        pairs = [(a, b) for a in range(1, modulus) for b in range(modulus)
                 if all((a * cipher[i] + b) % modulus == proposed[i]
                        for i in range(slot, len(proposed), period))]
        allowed.append(pairs)
    return allowed


def count_and_forced(cipher, proposed, period, modulus):
    choices = compatible(cipher, proposed, period, modulus)
    counts = [len(slot) for slot in choices]
    total = 1
    for size in counts:
        total *= size
    if total == 0:
        return counts, 0, None
    length = len(proposed)
    forced = sum(len({(a * cipher[position] + b) % modulus for a, b in choices[position % period]}) == 1
                 for position in range(length, min(len(cipher), length * 2)))
    return counts, total, forced


def toy_check():
    # Independent literal key enumeration over F3 validates the product rule.
    small = [(a, b) for a in (1, 2) for b in range(3)]
    ciphers = ((0, 0, 0, 0, 0, 0), (0, 1, 2, 0, 2, 1), (0, 0, 2, 2, 1, 1))
    tally = 0
    for cipher in ciphers:
        for proposed in itertools.product(range(3), repeat=6):
            for period in (1, 2, 3):
                counts, analytical, _ = count_and_forced(cipher, proposed, period, 3)
                exhaustive = sum(all((key[i % period][0] * cipher[i] + key[i % period][1]) % 3 == proposed[i]
                                     for i in range(6))
                                 for key in itertools.product(small, repeat=period))
                assert analytical == exhaustive
                assert all(n in (0, 1, 2) for n in counts)
                tally += 1
    return {"cipher_patterns": len(ciphers), "plaintext_patterns_per_cipher": 3 ** 6,
            "periods": [1, 2, 3], "exact_count_comparisons": tally, "passed": True}


def planted_check():
    control = PLAN["planted_control"]
    trace = source(ROOT / f"exports/readings/{control['reading']}.csv").decode("utf-8-sig")
    plain = [int(row["output_index"]) for row in csv.DictReader(trace.splitlines())][:control["length"]]
    assert len(plain) == control["length"] == 24
    maps = [(entry["a"], entry["b"]) for entry in control["maps"]]
    cipher = [(pow(maps[i % 3][0], -1, 29) * (value - maps[i % 3][1])) % 29
              for i, value in enumerate(plain)]
    counts, total, forced = count_and_forced(cipher, plain[:12], control["period"], 29)
    assert counts == [1, 1, 1] and total == 1 and forced == 12
    assert compatible(cipher, plain[:12], 3, 29) == [[key] for key in maps]
    assert [((maps[i % 3][0] * value + maps[i % 3][1]) % 29) for i, value in enumerate(cipher)] == plain
    return {"reading": control["reading"], "runes": len(plain), "period": 3,
            "slot_counts": counts, "compatible_keys": total,
            "following_positions_forced": forced, "passed": True}


def produce():
    toy = toy_check()
    planted = planted_check()
    alphabet = json.loads(source(ROOT / "data/index.json"))["alphabet"]
    lookup = {item["rune"]: i for i, item in enumerate(alphabet)}
    known = json.loads(source(ROOT / "experiments/records/lp2-known-vigenere-keys/plan.json"))
    openings = [(item["id"], item["indices"]) for item in known["openings"]]
    assert len(openings) == 9 and all(len(indices) == 12 for _, indices in openings)
    cases = []
    by_period = {str(period): {"impossible": 0, "unique": 0, "ambiguous": 0,
                          "compatible_key_max": 0, "forced_next12_sum": 0} for period in range(1, 9)}
    for page_id in PLAN["pages"]:
        page = json.loads(source(ROOT / f"data/pages/{page_id}.json"))
        ciphertext = [lookup[r] for line in page["lines"] for r in line["raw"] if r in lookup]
        assert len(ciphertext) == page["rune_count"] and len(ciphertext) >= 24
        for opening_id, proposal in openings:
            for period in range(1, 9):
                slots, total, forced = count_and_forced(ciphertext[:24], proposal, period, 29)
                assert all(n in (0, 1, 28) for n in slots)
                status = "impossible" if total == 0 else "unique" if total == 1 else "ambiguous"
                by_period[str(period)][status] += 1
                by_period[str(period)]["compatible_key_max"] = max(by_period[str(period)]["compatible_key_max"], total)
                if forced is not None:
                    by_period[str(period)]["forced_next12_sum"] += forced
                cases.append({"page": page_id, "crib": opening_id, "period": period,
                              "slot_counts": slots, "compatible_keys": total,
                              "status": status, "following_positions_forced": forced})
    empty = json.loads(source(ROOT / "data/pages/lp2-50.json"))
    assert empty["rune_count"] == 0 and len(cases) == 55 * 9 * 8
    for period, row in by_period.items():
        assert sum(row[key] for key in ("impossible", "unique", "ambiguous")) == 55 * 9
    return {"schema": "liberpedia-periodic-affine-crib-capacity-v1",
            "plan_sha256": hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest(),
            "toy_control": toy, "planted_control": planted,
            "page_count": len(PLAN["pages"]), "crib_count": len(openings), "periods": list(range(1, 9)),
            "case_count": len(cases), "by_period": by_period, "cases": cases}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = produce()
    path = HERE / "results.json"
    if args.check:
        assert result == json.loads(path.read_text(encoding="utf-8"))
        print("PASS: all crib/key counts and controls match saved result")
    else:
        path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({"cases": result["case_count"], "by_period": result["by_period"]}))
