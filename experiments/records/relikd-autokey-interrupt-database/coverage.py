"""Map the actual scored runes, not just source-section membership, to site pages."""
import argparse
import hashlib
import json
from pathlib import Path

import control
import target

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RANGES = [("p0-2", 0, 2), ("p3-7", 3, 7), ("p8-14", 8, 14), ("p15-22", 15, 22),
          ("p23-26", 23, 26), ("p27-32", 27, 32), ("p33-39", 33, 39),
          ("p40-53", 40, 53), ("p54-55", 54, 55)]


def build():
    indices = target.source_indices()
    sections = target.source_sections()
    result = json.loads((HERE / "results.json").read_text(encoding="utf8"))
    out = []
    for name, first, last in RANGES:
        pages = []
        joined = []
        for i in range(first, last + 1):
            page = json.loads((ROOT / "data" / "pages" / f"lp2-{i:02d}.json").read_text(encoding="utf8"))
            data = [control.RUNES.index(c) for c in page["raw"] if c in control.RUNES]
            assert len(data) == page["rune_count"]
            pages.append((page["id"], len(data)))
            joined.extend(data)
        assert joined == sections[name], name
        used = set()
        called_used = set()
        for row in result["rows"]:
            if row["section"] != name:
                continue
            source_rune = 28 if row["inverse"] else 0
            stops = indices[name]["positions"][source_rune][:16]
            skipped = {stops[x - 1] for x in row["selected_occurrences"]}
            positions = {i for i in range(row["prefix_runes"]) if i not in skipped}
            used.update(positions)
            if row["source_called"]:
                called_used.update(positions)
        cursor = 0
        mapped = []
        for page, count in pages:
            all_count = sum(cursor <= i < cursor + count for i in used)
            called_count = sum(cursor <= i < cursor + count for i in called_used)
            mapped.append({"page": page, "page_runes": count, "scored_runes_any_file": all_count,
                           "scored_runes_called_file": called_count,
                           "state_any_file": "full" if count and all_count == count else ("partial" if all_count else "none"),
                           "state_called_file": "full" if count and called_count == count else ("partial" if called_count else "none")})
            cursor += count
        out.extend(mapped)
    return {"schema": "relikd-autokey-interrupt-coverage-v1", "timing": "Post-result exact scored-position audit; score outcomes unchanged.",
            "result_sha256": hashlib.sha256((HERE / "results.json").read_bytes()).hexdigest(),
            "pages": out}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    control.SOURCE = target.SOURCE = args.source_root.resolve()
    output = build()
    path = HERE / "coverage.json"
    if args.check:
        assert output == json.loads(path.read_text(encoding="utf8"))
    else:
        path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf8", newline="\n")
    for field in ("state_any_file", "state_called_file"):
        print(field, {x: sum(p[field] == x for p in output["pages"]) for x in ("full", "partial", "none")})
