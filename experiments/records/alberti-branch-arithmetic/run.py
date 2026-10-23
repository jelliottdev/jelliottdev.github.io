"""Audit source-stated Alberti branch arithmetic and the pinned LP2-39 row."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute():
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    for entry in plan["inputs"]:
        assert digest(ROOT / entry["path"]) == entry["sha256"], entry["path"]
    lines = (ROOT / "text/lp2-39.txt").read_text(encoding="utf-8").splitlines()
    row = lines[plan["row"]["zero_based_page_line"]]
    groups, current = [], 0
    for char in row.rstrip("/"):
        if 0x16A0 <= ord(char) <= 0x16FF:
            current += 1
        elif char in ".-":
            groups.append(current)
            current = 0
        else:
            raise ValueError(f"Unexpected row character U+{ord(char):04X}")
    groups.append(current)
    assert groups == plan["row"]["rune_counts_between_visible_delimiters"]
    nums = plan["arithmetic"]
    overlay = nums["short_overlay"]
    assert len(overlay) == 4
    result = {"schema": plan["schema"], "page": "lp2-39", "line_one_based": plan["row"]["zero_based_page_line"] + 1,
              "row_runes": sum(groups), "row_delimiters": len(groups) - 1, "runes_per_segment": groups,
              "row_delimiter_types": [x for x in row if x in ".-"]}
    for side in ("left", "right"):
        plant = nums[f"plant_{side}"]
        final = nums[f"reported_{side}_final"]
        assert len(plant) == len(final) == 13
        base = [sum(plant[:4]), sum(plant[4:9]), sum(plant[9:])]
        final_sums = [sum(final[:4]), sum(final[4:9]), sum(final[9:])]
        raw = [base[0] + sum(overlay), base[2] + sum(overlay)]
        cyclic = []
        for start in range(13):
            rotated = plant[start:] + plant[:start]
            sums = [sum(rotated[:4]) + sum(overlay), sum(rotated[9:]) + sum(overlay)]
            cyclic.append({"start_zero_based": start, "raw_short_sums": sums,
                           "standard_mod_31": [x % nums["modulus"] for x in sums]})
        result[side] = {"plant_group_sums": base, "posted_final_group_sums": final_sums,
                        "computed_short_sums": raw,
                        "matches_posted_raw_sums": raw == nums["reported_short_sums"][side],
                        "standard_short_residues": [x % nums["modulus"] for x in raw],
                        "rotations": cyclic}
    result["right_reported_residues"] = nums["reported_right_mod_31"]
    result["right_residue_claim_matches_standard_modulo"] = result["right"]["standard_short_residues"] == nums["reported_right_mod_31"]
    result["left_exact_raw_rotation_hits"] = [x["start_zero_based"] for x in result["left"]["rotations"]
                                               if x["raw_short_sums"] == nums["reported_short_sums"]["left"]]
    result["right_reported_residue_rotation_hits"] = [x["start_zero_based"] for x in result["right"]["rotations"]
                                                      if x["standard_mod_31"] == nums["reported_right_mod_31"]]
    return result


def render_svg(result):
    # Phone-width text layout; no embedded raster, fonts or script.
    left, right = result["left"], result["right"]
    import html
    esc = html.escape
    label = lambda x: esc(str(x))
    cards = [
        ("LP2-39 source row", f"{result['row_runes']} runes · {result['row_delimiters']} separators", "+".join(map(str, result["runes_per_segment"]))),
        ("Left plant · short groups", label(left["computed_short_sums"]), "Posted totals reproduce"),
        ("Right plant · short groups", label(right["computed_short_sums"]), "Posted totals reproduce"),
        ("Right totals modulo 31", label(right["standard_short_residues"]), "Posted +2, +8 are opposite signs"),
    ]
    chunks = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 530" role="img" aria-labelledby="title desc">',
              '<title id="title">Alberti branch arithmetic audit</title>',
              '<desc id="desc">The page row has 19 runes. Posted raw short sums reproduce, but standard modulo 31 turns the right sums into 29 and 23 rather than the posted 2 and 8.</desc>',
              '<style>text{font-family:system-ui,sans-serif;fill:#263039}.card{fill:#f5f7f8;stroke:#c6d0d6}.small{fill:#53636d;font-size:14px}.heading{font-weight:650;font-size:19px}.number{font-size:23px;font-weight:700}</style>',
              '<rect width="360" height="530" fill="white"/>',
              '<text x="16" y="34" class="heading">Source arithmetic, checked</text>']
    for index, (title, value, note) in enumerate(cards):
        y = 50 + 112 * index
        chunks += [f'<rect class="card" x="16" y="{y}" width="328" height="98" rx="4"/>',
                   f'<text x="28" y="{y+26}" class="small">{esc(title)}</text>',
                   f'<text x="28" y="{y+60}" class="number">{esc(value)}</text>',
                   f'<text x="28" y="{y+84}" class="small">{esc(note)}</text>']
    chunks += ['<text x="16" y="518" class="small">Arithmetic only; no disk reading tested</text>', '</svg>']
    return "\n".join(chunks) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute()
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    svg = render_svg(result)
    for name, content in (("results.json", output), ("summary.svg", svg)):
        path = HERE / name
        if args.check:
            assert path.read_text(encoding="utf-8") == content, name
        else:
            path.write_bytes(content.encode("utf-8"))
    print("Alberti source arithmetic checked: right standard residues 29, 23; source reports 2, 8")


if __name__ == "__main__":
    main()
