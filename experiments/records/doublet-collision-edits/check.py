"""Independent run-based check of the three fixed collision edits."""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
from itertools import groupby, product
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
ALPHABET = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᛠᛡᚣ"


def blocks(s):
    return [(glyph, len(list(group))) for glyph, group in groupby(s)]


def check() -> None:
    assert sha256((HERE / "plan.json").read_bytes()).hexdigest() == DATA["plan_sha256"]
    assert len(DATA["inputs"]) == 56
    page_streams = []
    for entry in DATA["inputs"]:
        raw = (ROOT / entry["path"]).read_bytes()
        assert sha256(raw).hexdigest() == entry["sha256"]
        page_streams.append("".join(ch for ch in raw.decode("utf-8") if ch in ALPHABET))
    for name, report in DATA["rules"].items():
        fresh = []
        for page_number, original in enumerate(page_streams):
            output = []
            for glyph, n in blocks(original):
                if name == "delete_later":
                    output.append(glyph)
                else:
                    filler = ALPHABET[0] if name == "insert_fixed_f" else ALPHABET[(ALPHABET.index(glyph) + 1) % 29]
                    output.append((glyph + filler) * (n - 1) + glyph)
            edited = "".join(output)
            count = lambda s: sum(n - 1 for _, n in blocks(s))
            fresh.append({"page": f"lp2-{page_number:02d}", "input_runes": len(original), "input_doublets": count(original), "output_runes": len(edited), "output_doublets": count(edited)})
        assert fresh == report["pages"]
        for field in ("input_runes", "input_doublets", "output_runes", "output_doublets"):
            assert sum(x[field] for x in fresh) == report[field]
        assert report["output_runes"] - report["input_runes"] == ( -86 if name == "delete_later" else 86)
        for row in report["toy_ambiguity"]["by_length"]:
            n = row["original_length"]
            inverse = defaultdict(list)
            for glyphs in product(ALPHABET[:3], repeat=n):
                original = "".join(glyphs)
                edited = []
                for glyph, length in blocks(original):
                    if name == "delete_later":
                        edited.append(glyph)
                    else:
                        filler = ALPHABET[0] if name == "insert_fixed_f" else ALPHABET[(ALPHABET.index(glyph) + 1) % 29]
                        edited.append((glyph + filler) * (length - 1) + glyph)
                inverse["".join(edited)].append(original)
            assert row["originals"] == 3 ** n
            assert row["distinct_outputs"] == len(inverse)
            assert row["ambiguous_outputs"] == sum(len(v) > 1 for v in inverse.values())
            assert row["largest_preimage"] == max(map(len, inverse.values()))
    print("Independent run-based reconstruction matches all 56 pages, totals and toy preimages")


if __name__ == "__main__":
    check()
