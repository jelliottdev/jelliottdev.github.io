"""Recount all eight committed autokey interruption databases, without a new skip search."""
import argparse
import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path

import control

HERE = Path(__file__).resolve().parent
PLAN = control.PLAN
PLAN_SHA = control.PLAN_SHA
RUNES = control.RUNES
SOURCE = control.SOURCE


def source_indices():
    entries = {}
    for line in control.blob("db/db_indices.txt").decode("utf8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        name, total, rune, positions = line.split("|")
        record = entries.setdefault(name, {"total": int(total), "positions": {}})
        record["positions"][int(rune)] = [int(x) for x in positions.split(",") if x]
    return entries


def source_sections():
    return {name: [RUNES.index(c) for c in control.blob("pages/" + name + ".txt").decode("utf8") if c in RUNES]
            for name in PLAN["sections"]}


def setting(filename):
    name = Path(filename).stem.split("autokey_")[1]
    return {"operation": name[:2], "inverse": name.endswith("_inv")}


def recount():
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE).decode().strip() == PLAN["source_revision"]
    indices = source_indices()
    sections = source_sections()
    assert all(len(data) == indices[name]["total"] for name, data in sections.items())
    rows = []
    for filename in PLAN["files"]:
        rule = setting(filename)
        sign = 1 if rule["operation"][0] == "+" else -1
        function = rule["operation"][1]
        for line_number, line in enumerate(control.blob(filename).decode("utf8").splitlines(), 1):
            if not line.strip() or line.startswith("#"):
                continue
            name, n_interrupts, saved_score, irp, primer_field, skip_text = line.split("|")
            assert name in sections
            source_interrupt_index = 28 if rule["inverse"] else 0
            assert int(irp) == 0
            source_positions = indices[name]["positions"][source_interrupt_index]
            prefix_len = source_positions[16] if len(source_positions) > 16 else indices[name]["total"]
            stops = source_positions[:16]
            assert len(stops) == int(n_interrupts), (filename, line_number, len(stops), n_interrupts)
            skip_occurrences = [int(x) for x in skip_text.split(",") if x]
            assert skip_occurrences == sorted(set(skip_occurrences))
            assert all(1 <= x <= len(stops) for x in skip_occurrences)
            skipped_positions = {stops[x - 1] for x in skip_occurrences}
            transformed = [28 - x if rule["inverse"] else x for x in sections[name][:prefix_len]]
            input_after_skips = [x for i, x in enumerate(transformed) if i not in skipped_positions]
            primer = 1 if int(primer_field) == 0 else int(primer_field)
            decoded = control.decrypt(input_after_skips, primer, sign, function)
            score = control.ioc(decoded)
            delta = score - float(saved_score)
            rows.append({"file": filename, "line": line_number, "section": name, "source_called": filename.endswith("_-p.txt"),
                         "operation": rule["operation"], "inverse": rule["inverse"],
                         "interrupt_count": len(stops), "selected_skip_count": len(skipped_positions),
                         "selected_occurrences": skip_occurrences, "primer_field": int(primer_field), "effective_primer": primer,
                         "prefix_runes": prefix_len, "scored_runes": len(decoded), "saved_score": float(saved_score),
                         "recounted_score": score, "score_delta": delta,
                         "decoded_sha256": hashlib.sha256(bytes(decoded)).hexdigest()})
    groups = defaultdict(list)
    for row in rows:
        groups[(row["file"], row["section"])].append(row)
    maxima = []
    for (filename, section), group in sorted(groups.items()):
        best = max(x["saved_score"] for x in group)
        maxima.append({"file": filename, "section": section, "row_count": len(group), "saved_maximum": best,
                       "top_lines": [x["line"] for x in group if x["saved_score"] == best]})
    return {"schema": "relikd-autokey-interrupt-results-v1", "plan_sha256": PLAN_SHA,
            "row_count": len(rows), "score_abs_error_max": max(abs(x["score_delta"]) for x in rows),
            "within_print_precision": sum(abs(x["score_delta"]) <= 5.00001e-6 for x in rows),
            "file_section_maxima": maxima, "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    SOURCE = control.SOURCE = args.source_root.resolve()
    result = recount()
    path = HERE / "results.json"
    if args.check:
        assert json.loads(path.read_text(encoding="utf8")) == result
    else:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8", newline="\n")
    print("rows", result["row_count"], "within printed precision", result["within_print_precision"], "max error", result["score_abs_error_max"])
