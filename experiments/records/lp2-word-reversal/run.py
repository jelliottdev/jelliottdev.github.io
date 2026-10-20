"""Reverse runes within declared segments, preserving segment order.

Two explicit conventions: stop at every non-rune, or ignore / and line
breaks before locating segments. No guessed word boundaries or substitutions.
Run from any directory with Python 3; only standard-library modules are used.
"""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def segments(text, lookup, join_lines):
    """Return source-character offsets for each maximal declared rune segment."""
    groups, current = [], []
    for offset, character in enumerate(text):
        if character in lookup:
            current.append(offset)
        elif join_lines and character in "/\r\n":
            continue
        elif current:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def run():
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    for item in plan["inputs"]:
        if digest(ROOT / item["path"]) != item["sha256"]:
            raise ValueError("Input changed: " + item["path"])
    alphabet = [
        item["rune"]
        for item in json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    ]
    lookup = {rune: index for index, rune in enumerate(alphabet)}
    pages = []
    for page_id in plan["pages"]:
        text = (ROOT / "text" / (page_id + ".txt")).read_bytes().decode("utf-8")
        if {c for c in text if "\u16a0" <= c <= "\u16ff"} - set(alphabet):
            raise ValueError("Unknown rune in " + page_id)
        source = [i for i, c in enumerate(text) if c in lookup]
        ordinal = {offset: i for i, offset in enumerate(source)}
        cases = []
        if source:
            for mode in plan["boundary_modes"]:
                groups = segments(text, lookup, mode == "join-lines")
                order = [offset for group in groups for offset in reversed(group)]
                assert sorted(order) == source
                output = [lookup[text[offset]] for offset in order]
                cases.append({
                    "boundary_mode": mode,
                    "segment_lengths": [len(group) for group in groups],
                    "source_ordinals": [ordinal[offset] for offset in order],
                    "source_character_offsets": order,
                    "output_indices": output,
                    "matching_openings": [
                        opening["id"] for opening in plan["openings"]
                        if output[:12] == opening["indices"]
                    ],
                })
        pages.append({"page": page_id, "rune_count": len(source), "cases": cases})
    return {
        "schema": "liberpedia-word-reversal-v1",
        "plan_sha256": digest(HERE / "plan.json"),
        "pages": pages,
        "case_count": sum(len(page["cases"]) for page in pages),
        "comparison_count": sum(len(page["cases"]) for page in pages) * len(plan["openings"]),
        "distinct_page_outputs": sum(
            len({tuple(case["output_indices"]) for case in page["cases"]}) for page in pages
        ),
        "matching_case_count": sum(
            bool(case["matching_openings"]) for page in pages for case in page["cases"]
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--check", action="store_true")
    choice.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run()
    if args.check:
        if result != json.loads((HERE / "results.json").read_text(encoding="utf-8")):
            raise SystemExit("Rerun differs from the stored result.")
        print("Every segment, source trace and candidate reproduces exactly.")
    else:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, ensure_ascii=True, separators=(",", ":"))
            stream.write("\n")
    print(json.dumps({key: value for key, value in result.items() if key.endswith("count") or key == "distinct_page_outputs"}))


if __name__ == "__main__":
    main()
