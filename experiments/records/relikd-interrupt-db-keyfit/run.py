"""Reproduce the pinned unreachable interrupt/key-fit branch after explicit extraction."""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
PLAN_BYTES = (HERE / "plan.json").read_bytes()
PLAN = json.loads(PLAN_BYTES)
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"


def blob(source_root, name):
    raw = subprocess.check_output(["git", "show", "HEAD:" + name], cwd=source_root)
    assert hashlib.sha256(raw).hexdigest() == PLAN["source_sha256"][name], name
    return raw


def source_classes(source_root, temp):
    names = ["utils.py", "KeySearch.py", "RuneSolver.py", "RuneText.py", "Rune.py", "Alphabet.py"]
    for name in names:
        origin = "LP/" + name
        (temp / name).write_bytes(blob(source_root, origin))
    sys.path.insert(0, str(temp))
    return importlib.import_module("KeySearch"), importlib.import_module("RuneSolver"), importlib.import_module("RuneText")


def model(source_root):
    counts = {RUNES.index(r): int(n) for r, n in (line.split() for line in blob(source_root, "data/p-1gram.txt").decode("utf8").splitlines())}
    total = sum(counts.values())
    expect = [counts.get(i, 0) / total for i in range(29)]

    def similarity(values):
        bins = [0] * 29
        for value in values:
            bins[value] += 1
        return sum((bins[i] / len(values) - expect[i]) ** 2 for i in range(29))

    return similarity


def index_data(source_root):
    saved = {}
    for line in blob(source_root, "db/db_indices.txt").decode("utf8").splitlines():
        if line.startswith("#") or not line:
            continue
        name, total, rune, indices = line.split("|")
        if int(rune) != 0 or name not in {row["section"] for row in PLAN["candidate_rows"]}:
            continue
        saved[name] = (int(total), [int(x) for x in indices.split(",")] if indices else [])
    return saved


def source_rows(source_root):
    found = []
    for number, line in enumerate(blob(source_root, "db/db_norm.txt").decode("utf8").splitlines(), 1):
        if line.startswith("#") or not line:
            continue
        name, count, score, rune, keylen, skips = line.split("|")
        if name in {"p0-2", "p27-32", "p40-53"} and float(score) >= 0.55 and int(rune) == 0:
            found.append({"source_line": number, "section": name, "interrupt_count": int(count),
                          "saved_interrupt_score": float(score), "interrupt_index": int(rune),
                          "key_length": int(keylen),
                          "skip_occurrences": [int(x) for x in skips.split(",")] if skips else []})
    assert found == PLAN["candidate_rows"]
    return found


def fit_and_decode(source_key, source_solver, source_text, branch, nums, keylen, skips, similarity):
    fitter = source_key.GuessVigenere if branch == "Vigenere" else source_key.GuessAffine
    score, key = fitter(nums).guess(keylen, similarity)
    solver = source_solver.VigenereSolver() if branch == "Vigenere" else source_solver.AffineSolver()
    solver.INTERRUPT = RUNES[0]
    solver.INTERRUPT_POS = skips
    solver.KEY_DATA = key
    return float(score), key, solver


def controls(source_root, source_key, source_solver, source_text, similarity):
    authentic = [RUNES.index(c) for c in blob(source_root, "pages/p57_parable.txt").decode("utf8") if c in RUNES]
    assert len(authentic) == 95
    original = [RUNES.index(c) for c in blob(source_root, "_solved.txt").decode("utf8") if c in RUNES]
    sample_lengths = [(419, 14), (416, 26), (472, 20)]
    out = {"authentic": [], "matched_length": [], "skip_fixture": []}
    for branch in ("Vigenere", "Affine"):
        score, key, solver = fit_and_decode(source_key, source_solver, source_text, branch, authentic, 1, [], similarity)
        restored = solver.run(source_text.RuneText(authentic))[0].index_no_white
        out["authentic"].append({"branch": branch, "key": key, "score": score,
                                  "exact": restored == authentic})
        for length, keylen in sample_lengths:
            plain = original[:length]
            assert len(plain) == length
            shifts = [(7 * j + 3) % 29 for j in range(keylen)]
            multiples = [((5 * j + 1) % 28) + 1 for j in range(keylen)]
            cipher = [((p + shifts[i % keylen]) if branch == "Vigenere" else
                       (p * multiples[i % keylen] + shifts[i % keylen])) % 29 for i, p in enumerate(plain)]
            score, key, solver = fit_and_decode(source_key, source_solver, source_text, branch, cipher, keylen, [], similarity)
            restored = solver.run(source_text.RuneText(cipher))[0].index_no_white
            expected_key = shifts if branch == "Vigenere" else list(zip(multiples, shifts))
            out["matched_length"].append({"branch": branch, "runes": length, "key_length": keylen,
                                           "mean_similarity": score,
                                           "key_slots_exact": sum(tuple(a) == tuple(b) if isinstance(a, tuple) else a == b for a, b in zip(key, expected_key)),
                                           "full_key_exact": key == expected_key,
                                           "plaintext_runes_exact": sum(a == b for a, b in zip(restored, plain)),
                                           "full_plaintext_exact": restored == plain})
    # A skipped second F must be preserved and must not advance the key clock.
    fixture = [0, 4, 0, 7, 8, 0, 16]
    for branch in ("Vigenere", "Affine"):
        solver = source_solver.VigenereSolver() if branch == "Vigenere" else source_solver.AffineSolver()
        solver.INTERRUPT = RUNES[0]
        solver.INTERRUPT_POS = [2]
        solver.KEY_DATA = [1, 2] if branch == "Vigenere" else [(1, 1), (1, 2)]
        got = solver.run(source_text.RuneText(fixture))[0].index_no_white
        manual = []
        clock = 0
        seen_f = 0
        for value in fixture:
            if value == 0:
                seen_f += 1
            if value == 0 and seen_f == 2:
                manual.append(value)
            else:
                manual.append((value - (clock % 2 + 1)) % 29)
                clock += 1
        out["skip_fixture"].append({"branch": branch, "source_output": got,
                                    "manual_output": manual, "exact": got == manual})
    return out


def target(source_root, source_key, source_solver, source_text, similarity):
    positions = index_data(source_root)
    outputs = []
    for row in source_rows(source_root):
        section = row["section"]
        full = [RUNES.index(c) for c in blob(source_root, f"pages/{section}.txt").decode("utf8") if c in RUNES]
        total, f_positions = positions[section]
        assert total == len(full) and f_positions == [i for i, x in enumerate(full) if x == 0]
        stops = f_positions[:row["interrupt_count"]]
        upto = f_positions[row["interrupt_count"]] if len(f_positions) > row["interrupt_count"] else total
        assert all(1 <= x <= len(stops) for x in row["skip_occurrences"])
        # Source pops chosen positions from the capped fit prefix, in reverse order.
        fit = full[:upto]
        for occurrence in reversed(row["skip_occurrences"]):
            fit.pop(stops[occurrence - 1])
        for option in PLAN["operators"]:
            branch = option["name"]
            score, key, solver = fit_and_decode(source_key, source_solver, source_text, branch, fit,
                                                row["key_length"], row["skip_occurrences"], similarity)
            decoded = solver.run(source_text.RuneText(full))[0].index_no_white
            outputs.append({"source_line": row["source_line"], "section": section,
                            "key_length": row["key_length"], "saved_interrupt_score": row["saved_interrupt_score"],
                            "skip_occurrences": row["skip_occurrences"], "fit_prefix_runes": upto,
                            "fit_after_skips": len(fit), "full_section_runes": len(full),
                            "branch": branch, "mean_similarity": score,
                            "source_key_threshold": option["mean_similarity_limit"],
                            "source_reported": score <= option["mean_similarity_limit"],
                            "key": key, "decoded_sha256": hashlib.sha256(bytes(decoded)).hexdigest(),
                            "decoded_prefix_indices": decoded[:80]})
    return outputs


def produce(source_root, phase):
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source_root, text=True).strip() == PLAN["source_revision"]
    source_rows(source_root)
    with tempfile.TemporaryDirectory() as directory:
        modules = source_classes(source_root, Path(directory))
        similarity = model(source_root)
        out = {"plan_sha256": hashlib.sha256(PLAN_BYTES).hexdigest(),
               "controls": controls(source_root, *modules, similarity)}
        if phase == "all":
            out["target"] = target(source_root, *modules, similarity)
        return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--phase", choices=("controls", "all"), default="controls")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = produce(args.source_root.resolve(), args.phase)
    path = HERE / ("controls.json" if args.phase == "controls" else "results.json")
    if args.check:
        assert json.loads(json.dumps(output)) == json.loads(path.read_text(encoding="utf8"))
    else:
        path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf8", newline="\n")
    print("authentic", [(r["branch"], r["exact"]) for r in output["controls"]["authentic"]])
    print("matched", [(r["branch"], r["runes"], r["key_length"], r["full_plaintext_exact"]) for r in output["controls"]["matched_length"]])
    print("skip", [(r["branch"], r["exact"]) for r in output["controls"]["skip_fixture"]])
    if "target" in output:
        print("source-reported", sum(r["source_reported"] for r in output["target"]), "of", len(output["target"]))


if __name__ == "__main__":
    main()
