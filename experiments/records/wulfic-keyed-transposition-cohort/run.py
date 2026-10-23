#!/usr/bin/env python3
"""Replay one pinned public transposition grid on its actual rune streams.

The source is executed only after an exact SHA-256 check. It can be supplied
locally with --source-file or fetched from the pinned GitHub revision.
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
REV = PLAN["source_revision"]
URL = f"https://raw.githubusercontent.com/Wulfic/Cicada3301-Liber_Primus/{REV}/{PLAN['source_file']}"


def source_namespace(source_file=None):
    if source_file:
        raw = Path(source_file).read_bytes()
    else:
        with urllib.request.urlopen(URL, timeout=30) as response:
            raw = response.read()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != PLAN["source_sha256"]:
        raise ValueError(f"source SHA-256 mismatch: {digest}")
    ns = {"__name__": "pinned_wulfic_transposition", "__file__": str(source_file or URL)}
    exec(compile(raw, str(source_file or URL), "exec"), ns)
    # The pinned Git tree has no data/wordlist.txt. Force its declared
    # embedded-word fallback, independent of files in a reader's checkout.
    ns["DATA_DIR"] = HERE / "no_external_wordlist"
    ns["load_words"]()
    return ns


def load_current_pages(ns):
    mapping = {}
    rune_map = ns["RUNE_TO_IDX"]
    for global_page, page_id in zip(PLAN["source_page_numbers"], PLAN["current_page_ids"]):
        data = json.loads((ROOT / "data" / "pages" / f"{page_id}.json").read_text(encoding="utf-8"))
        raw = data["raw"]
        indices = [rune_map[ch] for ch in raw if ch in rune_map]
        if len(indices) != data["rune_count"]:
            raise ValueError(f"rune count mismatch for {page_id}")
        mapping[global_page] = (indices, raw)
    ns["load_runes"] = lambda p: mapping[p]
    return mapping


def enc_columnar(plain, width, col_to_rank):
    return [plain[i] for rank in range(width)
            for col in range(width) if col_to_rank[col] == rank
            for i in range(col, len(plain), width)]


def positive_controls(ns, mapping):
    checks = []
    for global_page, (real, _) in mapping.items():
        length = len(real)
        planted = [(i * 7 + 3) % 29 for i in range(length)]
        keyword = ns["PAGE_KEYS"][global_page]["keyword"]
        width = len(keyword)
        rank = ns["keyword_column_permutation"](keyword)
        cipher = enc_columnar(planted, width, rank)
        restored = ns["undo_columnar_transposition"](cipher, width, rank)
        checks.append({"page": global_page, "method": "keyword_columnar", "pass": restored == planted})
        magic = ns["magic_square_permutation"](planted)
        restored = ns["magic_square_inverse_permutation"](magic)
        checks.append({"page": global_page, "method": "magic_square_inverse", "pass": restored == planted})
        for method in ("snake_read", "diagonal_read", "spiral_read", "undo_spiral", "rail_fence_decrypt", "every_nth"):
            output = ns[method](planted, 5)
            checks.append({"page": global_page, "method": method + "_permutation", "pass": len(output) == length and sorted(output) == sorted(planted)})
    return checks


def build(source_file=None):
    ns = source_namespace(source_file)
    mapping = load_current_pages(ns)
    controls = positive_controls(ns, mapping)
    pages = []
    for global_page, page_id in zip(PLAN["source_page_numbers"], PLAN["current_page_ids"]):
        source_rows = ns["solve_page"](global_page, verbose=False)
        pages.append({
            "source_page": global_page,
            "current_page": page_id,
            "runes": len(mapping[global_page][0]),
            "source_row_count": len(source_rows),
            "best": {"method": source_rows[0][0], "score": source_rows[0][1], "preview": source_rows[0][4]},
            "baseline_score": next(row[1] for row in source_rows if row[0] == "NO_TRANSPOSITION"),
            "rows": [{"method": r[0], "score": r[1], "matched": r[2], "tokens": r[3], "preview": r[4]}
                     for r in source_rows],
        })
    return {
        "schema": "liberpedia-source-transposition-v1",
        "plan_sha256": hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest(),
        "source_sha256": PLAN["source_sha256"],
        "wordset_size": len(ns["WORD_SET"]),
        "controls": controls,
        "pages": pages,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-file", help="Exact pinned transposition_solver.py (otherwise fetch pinned revision)")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build(args.source_file)
    if not all(x["pass"] for x in result["controls"]):
        raise SystemExit("positive control failure; inspect result before any manuscript inference")
    text = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    destination = HERE / "results.json"
    if args.check:
        if destination.read_text(encoding="utf-8") != text:
            raise SystemExit("results.json does not match fresh source replay")
        print(f"check passed: {len(result['pages'])} pages, {len(result['controls'])} controls")
    else:
        destination.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {destination}: {len(result['pages'])} pages, {len(result['controls'])} controls")


if __name__ == "__main__":
    main()
