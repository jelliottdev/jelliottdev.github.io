"""Known-reading recovery and pinned source-class parity before saved-row recount."""
import argparse
import ast
import hashlib
import itertools
import json
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf8"))
PLAN_SHA = hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest()
SOURCE = HERE.parents[3] / "source-cache" / "relikd-text"
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109)


def blob(name):
    raw = subprocess.check_output(["git", "show", f"{PLAN['source_revision']}:{name}"], cwd=SOURCE)
    assert hashlib.sha256(raw).hexdigest() == PLAN["source_sha256"][name], name
    return raw


def original_classes():
    namespace = {"itertools": itertools, "PROB_NORM": [], "TARGET_IOC": 1.78}
    for path, name in (("LP/InterruptSearch.py", "InterruptSearch"), ("LP/Probability.py", "Probability")):
        klass = next(x for x in ast.parse(blob(path).decode("utf8")).body if isinstance(x, ast.ClassDef) and x.name == name)
        exec(compile(ast.Module(body=[klass], type_ignores=[]), path, "exec"), namespace)
    return namespace["InterruptSearch"], namespace["Probability"]


def decrypt(data, primer, sign, function):
    previous = primer
    out = []
    for y in data:
        step = PRIMES[previous] if function == "p" else previous
        value = (y + sign * step) % 29
        out.append(value)
        previous = value
    return out


def encrypt(plain, primer, sign, function):
    previous = primer
    out = []
    for value in plain:
        step = PRIMES[previous] if function == "p" else previous
        out.append((value - sign * step) % 29)
        previous = value
    return out


def ioc(data):
    hist = Counter(data)
    n = len(data)
    return 29 * sum(v * (v - 1) for v in hist.values()) / (n * (n - 1))


def run():
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE).decode().strip() == PLAN["source_revision"]
    known = [RUNES.index(c) for c in blob("_solved.txt").decode("utf8") if c in RUNES][:96]
    assert len(known) == 96
    SourceSearch, SourceProbability = original_classes()
    rows = []
    for filename in PLAN["files"]:
        suffix = Path(filename).stem.split("autokey_")[1]
        operation = suffix[:2]
        inverse = suffix.endswith("_inv")
        sign = 1 if operation[0] == "+" else -1
        function = operation[1]
        transformed = encrypt(known, 7, sign, function)
        inserted = PLAN["known_control"]["injected_interrupt_raw_positions"]
        processed = transformed[:]
        for position in inserted:
            processed.insert(position, 0)
        raw = [(28 - x) % 29 for x in processed] if inverse else processed
        stops = [i for i, x in enumerate(raw) if x == (28 if inverse else 0)]
        assert len(stops) <= 16, (filename, len(stops))
        occurrence_ids = [stops.index(x) + 1 for x in inserted]
        assert all(raw[x] == (28 if inverse else 0) for x in inserted)
        src = SourceSearch(processed, irp=0, irp_stops=stops)
        joined = src.join(inserted)
        expected = [x for i, x in enumerate(processed) if i not in set(inserted)]
        assert joined == expected == transformed
        recovered = decrypt(joined, 7, sign, function)
        assert recovered == known
        candidates = [ioc(decrypt(joined, seed, sign, function)) for seed in range(29)]
        actual = ioc(recovered)
        source_score = SourceProbability.IC_w_keylen(recovered, 1)
        assert abs(actual - source_score) < 1e-12
        rows.append({"file": filename, "known_runes": len(known), "raw_runes": len(raw),
                     "interrupt_occurrences": len(stops), "selected_occurrences": occurrence_ids,
                     "all_known_runes_recovered": recovered == known, "source_score_parity": True,
                     "true_primer_score": actual, "fixed_skip_primer_rank": 1 + sum(x > actual for x in candidates),
                     "known_indices_sha256": hashlib.sha256(bytes(known)).hexdigest(),
                     "recovered_indices_sha256": hashlib.sha256(bytes(recovered)).hexdigest()})
    return {"schema": "relikd-autokey-interrupt-controls-v1", "plan_sha256": PLAN_SHA, "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    SOURCE = args.source_root.resolve()
    result = run()
    path = HERE / "control-results.json"
    if args.check:
        assert json.loads(path.read_text(encoding="utf8")) == result
    else:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8", newline="\n")
    print("recovered", sum(x["all_known_runes_recovered"] for x in result["rows"]), "of", len(result["rows"]),
          "source parity", sum(x["source_score_parity"] for x in result["rows"]))
