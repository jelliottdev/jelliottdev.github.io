"""Map the source's searched prefixes to actual manuscript pages and lines."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = json.loads((HERE / "target-plan.json").read_text(encoding="utf-8"))
RUNES = set("ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ")


def source_blob(source_root, name):
    raw = subprocess.check_output(["git", "show", "HEAD:" + name], cwd=source_root)
    assert hashlib.sha256(raw).hexdigest() == PLAN["source_blobs"][name], name
    return raw.decode("utf-8")


def page_row(page, budget):
    site_path = ROOT / "data" / "pages" / f"lp2-{page:02d}.json"
    data = json.loads(site_path.read_text(encoding="utf-8"))
    lines = data["lines"]
    line_counts = [sum(ch in RUNES for ch in line["raw"]) for line in lines]
    total = sum(line_counts)
    assert total == data["rune_count"]
    taken = min(total, budget)
    if total == 0:
        state = "empty"
    elif taken == total:
        state = "full"
    elif taken:
        state = "partial"
    else:
        state = "verified_only"
    last_line = None
    last_line_rune = None
    if taken:
        remaining = taken
        for line_number, count in enumerate(line_counts, 1):
            if remaining <= count:
                last_line = line_number
                last_line_rune = remaining
                break
            remaining -= count
        assert last_line is not None
    return {
        "page": data["id"], "state": state, "runes_used": taken,
        "runes_on_page": total, "last_used_line": last_line,
        "last_used_rune_on_line": last_line_rune,
    }, [ch for ch in data["raw"] if ch in RUNES][:taken], [ch for ch in data["raw"] if ch in RUNES]


def build(source_root):
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source_root, text=True).strip() == PLAN["source_revision"]
    sections = []
    searched_pages = []
    for section in PLAN["source_sections"]:
        low, high = map(int, re.fullmatch(r"p(\d+)-(\d+)", section).groups())
        raw = source_blob(source_root, f"pages/{section}.txt").strip()
        full_chars = [ch for ch in raw if ch not in "\r\n"]
        prefix = full_chars[:970]
        used_runes = [ch for ch in prefix if ch in RUNES]
        full_runes = [ch for ch in full_chars if ch in RUNES]
        remaining = len(used_runes)
        pages = []
        site_used = []
        site_full = []
        for page in range(low, high + 1):
            row, used, full = page_row(page, remaining)
            pages.append(row)
            site_used.extend(used)
            site_full.extend(full)
            remaining -= len(used)
            if row["runes_used"]:
                searched_pages.append(row["page"])
        assert remaining == 0
        assert site_full == full_runes, section
        assert site_used == used_runes, section
        sections.append({
            "section": section, "source_prefix_symbols": len(prefix),
            "source_prefix_runes": len(used_runes),
            "source_full_runes": len(full_runes), "pages": pages,
        })
    return {
        "schema": "relikd-rotated-key-prefix-coverage-v1",
        "timing": "Post-result scope audit; does not change the frozen source or target plans or numerical results.",
        "source_revision": PLAN["source_revision"],
        "rule": "Take the source section's first 970 non-newline symbols after strip, then retain runes. Map their rune order to the independently verified full site-page rune stream; a page contributes only if one of its runes survives the prefix.",
        "sections": sections,
        "searched_pages": searched_pages,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    receipt = build(args.source_root.resolve())
    path = HERE / "prefix-coverage.json"
    if args.check:
        assert receipt == json.loads(path.read_text(encoding="utf-8"))
    else:
        path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    for row in receipt["sections"]:
        used = [p for p in row["pages"] if p["runes_used"]]
        print(row["section"], row["source_prefix_runes"], "runes", ", ".join(f"{p['page']}:{p['runes_used']}/{p['runes_on_page']}" for p in used))
    print("searched pages", len(receipt["searched_pages"]))


if __name__ == "__main__":
    main()
