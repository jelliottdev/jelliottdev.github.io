"""Reproduce six Night Thoughts quote positions in pinned 1853 transcription."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORDS = re.compile(r"[A-Za-z]+")
NUMBER = re.compile(r"\s{2,}(\d{1,4})\s*$")


def normalized(value):
    return " ".join(WORDS.findall(value.lower()))


def stripped_line(value):
    return NUMBER.sub("", value).strip()


def find_number(lines, pos):
    anchors = []
    for direction in (-1, 1):
        for distance in range(1, 22):
            at = pos + direction * distance
            if at < 0 or at >= len(lines):
                continue
            match = NUMBER.search(lines[at])
            if match:
                anchor = int(match.group(1))
                inferred = anchor + (pos - at)
                anchors.append({"file_line_one_based": at + 1, "printed_number": anchor,
                                "inferred_target": inferred})
                break
    own = NUMBER.search(lines[pos])
    if own:
        anchors.append({"file_line_one_based": pos + 1, "printed_number": int(own.group(1)),
                        "inferred_target": int(own.group(1))})
    assert len(anchors) >= 2 and len({a["inferred_target"] for a in anchors}) == 1, anchors
    return anchors[0]["inferred_target"], anchors


def compute():
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    for item in plan["inputs"]:
        assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    lines = (ROOT / plan["inputs"][0]["path"]).read_text(encoding="utf-8-sig").splitlines()
    headings = {night: next(i for i, line in enumerate(lines) if line.strip() == f"NIGHT {night}.")
                for night in ("FOURTH", "FIFTH", "SIXTH", "SEVENTH", "NINTH")}
    headings["EIGHTH"] = next(i for i, line in enumerate(lines) if line.strip() == "NIGHT EIGHTH")
    order = [target["night"] for target in plan["targets"]]
    assert order == ["FOURTH", "FIFTH", "SIXTH", "SEVENTH", "EIGHTH", "NINTH"]
    rows = []
    for at, target in enumerate(plan["targets"]):
        start = headings[target["night"]] + 1
        stop = headings[order[at + 1]] if at + 1 < len(order) else len(lines)
        needle = normalized(target["locator"])
        matches = [i for i in range(start, stop) if needle in normalized(stripped_line(lines[i]))]
        assert len(matches) == 1, (target["night"], matches)
        pos = matches[0]
        number, anchors = find_number(lines, pos)
        rows.append({"night": target["night"], "reported_quote": target["reported_quote"],
                     "comparison_edition_line": stripped_line(lines[pos]),
                     "comparison_edition_file_line_one_based": pos + 1,
                     "comparison_edition_verse_line": number,
                     "matches_reported_729": number == plan["reported_pointer"],
                     "line_number_anchors": anchors})
    counts = []
    for entry in plan["inputs"][1:]:
        raw = (ROOT / entry["path"]).read_text(encoding="utf-8")
        counts.append({"page": Path(entry["path"]).stem,
                       "alphabet_runes": sum(0x16A0 <= ord(ch) <= 0x16FF for ch in raw)})
    return {"schema": plan["schema"], "book_comparison": plan["comparison_edition"],
            "rune_counts": counts, "rune_total": sum(x["alphabet_runes"] for x in counts),
            "reported_pointer": plan["reported_pointer"], "line_matches": sum(x["matches_reported_729"] for x in rows),
            "candidates": rows}


def svg(result):
    names = {"FOURTH": "Night IV", "FIFTH": "Night V", "SIXTH": "Night VI", "SEVENTH": "Night VII", "EIGHTH": "Night VIII", "NINTH": "Night IX"}
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 478" role="img" aria-labelledby="title desc">',
             '<title id="title">Six reported Night Thoughts line-729 lookups</title>',
             '<desc id="desc">Five reported passages are line 729 in the pinned 1853 edition; the sixth, in Night IX, is line 731.</desc>',
             '<style>text{font-family:system-ui,sans-serif;fill:#253039}.small{font-size:14px;fill:#53636d}.name{font-size:16px;font-weight:600}.value{font-size:20px;font-weight:700}.rule{stroke:#cbd3d9}.wrong{fill:#8a3e36}</style>',
             '<rect width="360" height="478" fill="white"/>',
             '<text x="16" y="31" font-size="19" font-weight="650">Six passages, one later edition</text>',
             '<text x="16" y="54" class="small">Reported line: 729 in each Night</text>']
    for i, entry in enumerate(result["candidates"]):
        y = 73 + 55 * i
        parts += [f'<line x1="16" y1="{y}" x2="344" y2="{y}" class="rule"/>',
                  f'<text x="16" y="{y+27}" class="name">{names[entry["night"]]}</text>',
                  f'<text x="336" y="{y+27}" text-anchor="end" class="value{" wrong" if not entry["matches_reported_729"] else ""}">{entry["comparison_edition_verse_line"]}</text>']
    parts += ['<line x1="16" y1="403" x2="344" y2="403" class="rule"/>',
              '<text x="16" y="432" class="small">5 of 6 positions match in this edition.</text>',
              '<text x="16" y="456" class="small">The cited Google scan remains unverified.</text>', '</svg>']
    return "\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute()
    for name, content in (("results.json", json.dumps(result, ensure_ascii=False, indent=2) + "\n"),
                          ("line-729.svg", svg(result))):
        path = HERE / name
        if args.check:
            assert path.read_text(encoding="utf-8") == content, name
        else:
            path.write_bytes(content.encode("utf-8"))
    print(f"{result['line_matches']}/6 source-quoted passages are verse line 729 in the pinned 1853 edition")


if __name__ == "__main__":
    main()
