"""Locate LP2 doublets and test separator and stored-correction sensitivity."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CORRECTED = ("lp2-05", "lp2-07", "lp2-11", "lp2-15", "lp2-35", "lp2-37", "lp2-38")
CATEGORIES = ("contiguous", "row-wrap only", "apostrophe/soft wrap", "hyphen", "other separator")


def classify(between):
    if not between:
        return "contiguous"
    if set(between) <= set("/\r\n"):
        return "row-wrap only"
    if set(between) <= set("'/\r\n"):
        return "apostrophe/soft wrap"
    if "-" in between:
        return "hyphen"
    return "other separator"


def pairs(text, alphabet):
    unknown = {c for c in text if "\u16a0" <= c <= "\u16ff"} - alphabet
    if unknown:
        raise ValueError(f"Unknown Runic-block character: {unknown!r}")
    positions = [(i, c) for i, c in enumerate(text) if c in alphabet]
    results = []
    for rune_index, ((left_offset, left), (right_offset, right)) in enumerate(zip(positions, positions[1:])):
        between = text[left_offset + 1:right_offset]
        results.append({"rune_index_zero_based": rune_index,
                        "left_offset_zero_based": left_offset,
                        "right_offset_zero_based": right_offset,
                        "left_rune": left, "right_rune": right,
                        "between": between, "category": classify(between),
                        "equal": left == right})
    return positions, results


def counts(rows):
    return {category: sum(row["category"] == category for row in rows)
            for category in CATEGORIES}


def report():
    raw_index = (ROOT / "data/index.json").read_bytes()
    alphabet = {item["rune"] for item in json.loads(raw_index)["alphabet"]}
    assert len(alphabet) == 29
    hashes = {"data/index.json": hashlib.sha256(raw_index).hexdigest()}
    all_pairs, all_doublets, reviewed_pairs, reviewed_doublets = [], [], [], []
    changes = []
    pages = []
    for number in range(56):
        page = f"lp2-{number:02d}"
        path = f"text/{page}.txt"
        raw_bytes = (ROOT / path).read_bytes()
        raw = raw_bytes.decode("utf-8")
        hashes[path] = hashlib.sha256(raw_bytes).hexdigest()
        left_positions, original = pairs(raw, alphabet)
        reviewed = original
        if page in CORRECTED:
            page_path = f"data/pages/{page}.json"
            page_bytes = (ROOT / page_path).read_bytes()
            page_data = json.loads(page_bytes)
            assert page_data["raw"] == raw and page_data["reviewed_text"] != raw
            right_positions, reviewed = pairs(page_data["reviewed_text"], alphabet)
            assert [rune for _, rune in left_positions] == [rune for _, rune in right_positions]
            hashes[page_path] = hashlib.sha256(page_bytes).hexdigest()
            assert len(original) == len(reviewed)
        for old, new in zip(original, reviewed):
            assert old["equal"] == new["equal"]
            all_pairs.append(old)
            reviewed_pairs.append(new)
            if old["equal"]:
                event = {"page": page, **old,
                         "reviewed_between": new["between"],
                         "reviewed_category": new["category"]}
                all_doublets.append(event)
                reviewed_doublets.append(new)
                if old["category"] != new["category"]:
                    changes.append({"page": page, "rune_index_zero_based": old["rune_index_zero_based"],
                                    "from": old["category"], "to": new["category"]})
        pages.append({"page": page, "runes": len(left_positions),
                      "pairs": len(original), "doublets": sum(row["equal"] for row in original),
                      "has_stored_reviewed_layer": page in CORRECTED})
    categories = counts(all_doublets)
    reviewed_categories = counts(reviewed_doublets)
    return {
        "schema": "liberpedia-doublet-boundaries-v1",
        "scope": "Archived LP2-00--55 alphabet-rune streams including headings; within-page pairs only, non-runes removed for the primary 86-event count.",
        "input_sha256": hashes, "pages": pages,
        "archived": {"runes": sum(p["runes"] for p in pages),
                     "all_pairs": len(all_pairs), "doublets": len(all_doublets),
                     "category_all_pairs": counts(all_pairs),
                     "category_doublets": categories,
                     "within_token_pairs": sum(counts(all_pairs)[c] for c in CATEGORIES[:3]),
                     "within_token_doublets": sum(categories[c] for c in CATEGORIES[:3])},
        "reviewed_layer": {"pages_with_separate_layer": list(CORRECTED),
                           "all_pairs": len(reviewed_pairs), "doublets": len(reviewed_doublets),
                           "category_doublets": reviewed_categories,
                           "doublet_category_changes": changes},
        "page_join": "Joining the 55 nonempty filtered page streams adds 54 comparisons and zero equal pairs, as separately recorded in exports/unsolved-doublets.json.",
        "classification": {
            "contiguous": "The two rune characters are directly adjacent in the UTF-8 decoded page text.",
            "row-wrap only": "Only slash and CR/LF row-wrap marks intervene.",
            "apostrophe/soft wrap": "An apostrophe intervenes, possibly together with slash and CR/LF row-wrap marks.",
            "hyphen": "A hyphen intervenes; it may coexist with a row wrap.",
            "other separator": "A non-rune mark other than the preceding cases intervenes.",
            "token_rule": "Within-token means contiguous, row-wrap only, or apostrophe/soft wrap. This follows the published word-length convention of removing slash/CR/LF and permitting internal apostrophes; it is not an image-verified word boundary."},
        "events": all_doublets,
        "limitations": "Only seven LP2 pages have stored reviewed-text layers and none changes rune order. This is not a comparison with a second complete independent transcription or manual verification of all 86 source-image pairs."
    }


def figure(result):
    counts_by_category = result["archived"]["category_doublets"]
    colors = ["#285e75", "#799899", "#adc2b7", "#bd8d58", "#7f6f6a"]
    labels = {"contiguous": "No mark between runes", "row-wrap only": "Row wrap only",
              "apostrophe/soft wrap": "Apostrophe / soft wrap", "hyphen": "Hyphen (possibly with wrap)",
              "other separator": "Other punctuation"}
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="640" height="292" viewBox="0 0 640 292" role="img" aria-labelledby="title desc">',
             '<title id="title">Where the 86 LP2 equal-rune pairs occur</title>',
             '<desc id="desc">Sixty are contiguous, three cross only a row wrap, twenty-two cross a hyphen, and one crosses other punctuation. No doublet crosses an apostrophe or soft wrap alone.</desc>',
             '<rect width="640" height="292" fill="white"/>',
             '<g font-family="system-ui, sans-serif" fill="#263842">',
             '<text x="20" y="31" font-size="19">Where the 86 matching pairs occur</text>',
             '<text x="20" y="53" font-size="12">Intervening marks in the archived text · LP2-00–55</text>']
    x = 20
    for category, color in zip(CATEGORIES, colors):
        width = counts_by_category[category] * 6.9
        if width:
            parts.append(f'<rect x="{x:.1f}" y="70" width="{width:.1f}" height="29" fill="{color}"/>')
        x += width
    for i, (category, color) in enumerate(zip(CATEGORIES, colors)):
        y = 126 + 31 * i
        parts += [f'<rect x="20" y="{y-11}" width="14" height="14" fill="{color}"/>',
                  f'<text x="44" y="{y+1}" font-size="13">{labels[category]}</text>',
                  f'<text x="400" y="{y+1}" font-size="13">{counts_by_category[category]}</text>']
    parts += ['<text x="20" y="285" font-size="11">Classification uses stored separators; it does not verify marks against the scans.</text>',
              '</g></svg>']
    return "\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report()
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    chart = figure(result)
    if args.write:
        (HERE / "results.json").write_text(payload, encoding="utf-8", newline="\n")
        (HERE / "boundaries.svg").write_text(chart, encoding="utf-8", newline="\n")
    if args.check:
        assert payload == (HERE / "results.json").read_text(encoding="utf-8")
        assert chart == (HERE / "boundaries.svg").read_text(encoding="utf-8")
        print("PASS doublet positions, separator classes, reviewed-layer effects and figure")
    print(result["archived"])
    print(result["reviewed_layer"]["category_doublets"], result["reviewed_layer"]["doublet_category_changes"])


if __name__ == "__main__":
    main()
