"""Post-result exact page scope of the saved-row score calculations."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf8"))
RESULT = json.loads((HERE / "results.json").read_text(encoding="utf8"))
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
SECTIONS = [("p0-2", 0, 2), ("p3-7", 3, 7), ("p8-14", 8, 14), ("p15-22", 15, 22),
            ("p23-26", 23, 26), ("p27-32", 27, 32), ("p33-39", 33, 39),
            ("p40-53", 40, 53), ("p54-55", 54, 55)]


def build(source):
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source).decode().strip() == PLAN["source_revision"]

    def blob(name):
        raw = subprocess.check_output(["git", "show", "HEAD:" + name], cwd=source)
        assert hashlib.sha256(raw).hexdigest() == PLAN["source_sha256"][name]
        return raw

    indexes = {}
    for line in blob("db/db_indices.txt").decode("utf8").splitlines():
        if line.startswith("#") or not line:
            continue
        name, total, rune, text = line.split("|")
        indexes.setdefault(name, {})[int(rune)] = [int(x) for x in text.split(",") if x]
    sections = []
    all_used = []
    for name, first, last in SECTIONS:
        source_runes = [RUNES.index(x) for x in blob("pages/" + name + ".txt").decode("utf8") if x in RUNES]
        pages = []
        site_runes = []
        for i in range(first, last + 1):
            page = json.loads((ROOT / "data" / "pages" / f"lp2-{i:02d}.json").read_text(encoding="utf8"))
            data = [RUNES.index(x) for x in page["raw"] if x in RUNES]
            assert len(data) == page["rune_count"]
            pages.append((page["id"], len(data)))
            site_runes.extend(data)
        assert site_runes == source_runes, name
        scored_positions = set()
        for row in RESULT["rows"]:
            if row["section"] != name:
                continue
            filename = row["file"]
            irp = row["interrupt_index"]
            if "_mod_b_" in filename:
                part = filename.split("_mod_b_")[1].split(".")
                modulus, group = int(part[0]), int(part[1])
                positions = [(x - group) // modulus for x in indexes[name][irp] if x % modulus == group][:20]
                selected = {positions[n - 1] for n in row["skip_occurrences"]}
                selected_raw = [group + modulus * i for i in range(row["fit_prefix_runes"]) if i not in selected]
            else:
                positions = indexes[name][irp][:20]
                selected = {positions[n - 1] for n in row["skip_occurrences"]}
                selected_raw = [i for i in range(row["fit_prefix_runes"]) if i not in selected]
                if "_mod_a_" in filename:
                    part = filename.split("_mod_a_")[1].split(".")
                    modulus, group = int(part[0]), int(part[1])
                    selected_raw = selected_raw[group::modulus]
            scored_positions.update(selected_raw)
        last_used = max(scored_positions, default=-1)
        cursor = 0
        mapped = []
        for page, count in pages:
            overlap = sum(cursor <= position < cursor + count for position in scored_positions)
            state = "full" if overlap == count and count else ("partial" if overlap else "none")
            mapped.append({"page": page, "runes_on_page": count, "runes_used": overlap, "state": state})
            if overlap:
                all_used.append(page)
            cursor += count
        sections.append({"section": name, "full_runes": len(source_runes), "last_used_rune_index": last_used,
                         "pages": mapped})
    return {"schema": "relikd-interrupt-pattern-db-coverage-v1", "timing": "Post-result scope audit; no score or control changes.",
            "rule": "For every saved row, map non-skipped scored rune positions back through the exact source group/interrupt order, then take the union per section. A page counts as contributing only if a rune entered at least one source score.",
            "source_revision": PLAN["source_revision"], "result_sha256": hashlib.sha256((HERE / "results.json").read_bytes()).hexdigest(),
            "sections": sections, "contributing_pages": list(dict.fromkeys(all_used))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = build(args.source_root.resolve())
    path = HERE / "coverage.json"
    if args.check:
        assert output == json.loads(path.read_text(encoding="utf8"))
    else:
        path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf8", newline="\n")
    print("contributing pages", len(output["contributing_pages"]))
