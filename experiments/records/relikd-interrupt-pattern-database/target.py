"""Recount every committed mirror/modulo row; never search new skip sets."""

import hashlib
import argparse
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

import control
from control import PLAN, RUNES, blob, score, score_mirror

HERE = Path(__file__).resolve().parent
SOURCE = control.SOURCE
PLAN_SHA = hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest()


def source_indices():
    out = {}
    for line in blob("db/db_indices.txt").decode("utf8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        name, total, rune, positions = line.split("|")
        out.setdefault(name, {"total": int(total), "positions": {}})["positions"][int(rune)] = ([int(x) for x in positions.split(",")] if positions else [])
    return out


def raw_sections():
    out = {}
    for section in ("p0-2", "p3-7", "p8-14", "p15-22", "p23-26", "p27-32", "p33-39", "p40-53", "p54-55"):
        out[section] = [RUNES.index(c) for c in blob("pages/" + section + ".txt").decode("utf8") if c in RUNES]
    return out


def source_model_target():
    bins = [0] * 29
    for line in blob("data/p-1gram.txt").decode("utf8").splitlines():
        rune, count = line.split()
        bins[RUNES.index(rune)] = int(count)
    n = sum(bins)
    return 29 * sum(v * (v - 1) for v in bins) / (n * (n - 1))


def setting(filename):
    if "pattern_mirror" in filename:
        m = re.search(r"db_(high|norm)_pattern_mirror_([ab])\.([0-9]+)\.txt$", filename)
        assert m
        return {"family": "mirror", "kind": m[1], "variant": m[2], "phase": int(m[3])}
    m = re.search(r"db_(high|norm)_mod_([ab])_([23])\.([0-2])\.txt$", filename)
    assert m
    return {"family": "modulo_" + m[2], "kind": m[1], "modulus": int(m[3]), "subgroup": int(m[4])}


def cut_and_join(raw, positions, row, rule):
    irp = row["interrupt_index"]
    all_stops = positions["positions"][irp]
    if rule["family"] == "modulo_b":
        mod, mo = rule["modulus"], rule["subgroup"]
        group_stops = [(x - mo) // mod for x in all_stops if x % mod == mo]
        cutoff = group_stops[20] if len(group_stops) > 20 else (positions["total"] // mod + (mo < positions["total"] % mod))
        data = raw[mo::mod][:cutoff]
        stops = group_stops[:20]
    else:
        cutoff = all_stops[20] if len(all_stops) > 20 else positions["total"]
        data = raw[:cutoff]
        stops = all_stops[:20]
    assert row["interrupt_count"] == len(stops), (row, len(stops))
    selected = [stops[i - 1] for i in row["skip_occurrences"]]
    assert selected == sorted(set(selected))
    selected_set = set(selected)
    joined = [x for i, x in enumerate(data) if i not in selected_set]
    if rule["family"] == "modulo_a":
        joined = joined[rule["subgroup"]::rule["modulus"]]
    return joined, len(data), len(selected)


def compute():
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE).decode().strip() == PLAN["source_revision"]
    sections, indices, target = raw_sections(), source_indices(), source_model_target()
    assert all(len(raw) == indices[name]["total"] for name, raw in sections.items())
    rows = []
    for family, filenames in PLAN["families"].items():
        for filename in filenames:
            rule = setting(filename)
            assert rule["family"] == family
            for line_number, line in enumerate(blob(filename).decode("utf8").splitlines(), 1):
                if line.startswith("#") or not line.strip():
                    continue
                name, n_interrupts, saved_score, irp, keylen, skip_text = line.split("|")
                assert name in sections
                row = {"file": filename, "line": line_number, "section": name,
                       "interrupt_count": int(n_interrupts), "interrupt_index": int(irp),
                       "key_length": int(keylen), "skip_occurrences": [int(x) for x in skip_text.split(",")] if skip_text else [],
                       "saved_score": float(saved_score)}
                joined, prefix_runes, selected_skip_count = cut_and_join(sections[name], indices[name], row, rule)
                if family == "mirror":
                    generated_score = score_mirror(joined, row["key_length"], rule["variant"], rule["kind"], target)
                else:
                    generated_score = score(joined, row["key_length"], rule["kind"], target)
                row.update({"fit_prefix_runes": prefix_runes, "after_skip_runes": len(joined),
                            "selected_skip_count": selected_skip_count, "recounted_score": generated_score,
                            "score_delta": generated_score - row["saved_score"]})
                rows.append(row)
    by_file = defaultdict(list)
    for row in rows:
        by_file[(row["file"], row["section"])].append(row)
    maxima = []
    for (filename, section), group in sorted(by_file.items()):
        highest = max(x["saved_score"] for x in group)
        maxima.append({"file": filename, "section": section, "rows": len(group), "saved_max": highest,
                       "top_lines": [x["line"] for x in group if x["saved_score"] == highest]})
    return {"schema": "relikd-interrupt-pattern-db-results-v1", "plan_sha256": PLAN_SHA,
            "source_target_ioc": target, "row_count": len(rows), "file_section_maxima": maxima,
            "score_abs_error_max": max(abs(x["score_delta"]) for x in rows),
            "score_recount_within_5e-5": sum(abs(x["score_delta"]) <= 5e-5 for x in rows),
            "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    SOURCE = control.SOURCE = args.source_root.resolve()
    result = compute()
    path = HERE / "results.json"
    if args.check:
        assert json.loads(path.read_text(encoding="utf8")) == result
    else:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8", newline="\n")
    print(result["row_count"], "rows", result["score_recount_within_5e-5"], "within printed precision", result["score_abs_error_max"], "max discrepancy")
