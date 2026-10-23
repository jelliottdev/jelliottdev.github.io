"""Draw a compact mobile-first summary of source test power and exclusions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render() -> str:
    data = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    width = data["aa"]["width_rows"]
    blocks = data["z"]["block_by_length"]
    esc = lambda value: (str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 352 520" role="img" aria-labelledby="title desc">',
        '<title id="title">Repeat-preservation source test results</title>',
        '<desc id="desc">Stage AA excludes five of twenty-six context-width cells. Stage Z shows exclusions by aligned-block size and two word cells; gray cells lack enough control power.</desc>',
        '<rect width="352" height="520" fill="#f6f7f8"/>',
        '<text x="16" y="31" fill="#192832" font-family="Arial,sans-serif" font-size="17" font-weight="700">Can repeats rule a model out?</text>',
        '<text x="16" y="55" fill="#45545f" font-family="Arial,sans-serif" font-size="15">Blue: excluded · Gray: unresolved</text>',
        '<line x1="16" y1="70" x2="336" y2="70" stroke="#ccd3d8"/>',
        '<text x="16" y="96" fill="#192832" font-family="Arial,sans-serif" font-size="15" font-weight="700">Local context (AA)</text>',
    ]
    for idx, mode in enumerate(("sec", "cont")):
        group = sorted((r for r in width if r["mode"] == mode), key=lambda r: int(r["w"]))
        excluded = [r["w"] for r in group if r["verdict"] == "EXCLUDED"]
        y = 125 + idx * 54
        label = "Within sections" if mode == "sec" else "Joined stream"
        lines.append(f'<text x="16" y="{y}" fill="#263741" font-family="Arial,sans-serif" font-size="15">{label}</text>')
        lines.append(f'<text x="336" y="{y}" text-anchor="end" fill="#263741" font-family="Arial,sans-serif" font-size="15">{len(excluded)}/13</text>')
        for j, row in enumerate(group):
            color = "#2d5e79" if row["verdict"] == "EXCLUDED" else "#c4ccd1"
            lines.append(f'<rect x="{16 + j * 25}" y="{y + 9}" width="21" height="17" rx="2" fill="{color}"/>')
        lines.append(f'<text x="16" y="{y + 41}" fill="#55636c" font-family="Arial,sans-serif" font-size="15">width 0</text>')
        lines.append(f'<text x="336" y="{y + 41}" text-anchor="end" fill="#55636c" font-family="Arial,sans-serif" font-size="15">12</text>')
    lines += [
        '<line x1="16" y1="222" x2="336" y2="222" stroke="#ccd3d8"/>',
        '<text x="16" y="250" fill="#192832" font-family="Arial,sans-serif" font-size="15" font-weight="700">Fixed word / block codebooks (Z)</text>',
    ]
    word = data["z"]["word_cells"]
    labels = ", ".join("within" if r["cell"] == "Zw-sec" else "all" for r in word if r["verdict"] == "EXCLUDED")
    lines.append(f'<text x="16" y="277" fill="#263741" font-family="Arial,sans-serif" font-size="15">Repeated words: {esc(labels or "not excluded")}</text>')
    for idx, row in enumerate(blocks):
        y = 306 + idx * 27
        excluded = row["verdicts"].get("EXCLUDED", 0)
        total = row["total"]
        lines.append(f'<text x="16" y="{y}" fill="#263741" font-family="Arial,sans-serif" font-size="15">{row["n"]}-rune blocks</text>')
        lines.append(f'<rect x="135" y="{y - 11}" width="144" height="14" rx="2" fill="#c4ccd1"/>')
        lines.append(f'<rect x="135" y="{y - 11}" width="{144 * excluded / total:.2f}" height="14" rx="2" fill="#2d5e79"/>')
        lines.append(f'<text x="336" y="{y}" text-anchor="end" fill="#263741" font-family="Arial,sans-serif" font-size="15">{excluded}/{total}</text>')
    lines += [
        '<line x1="16" y1="489" x2="336" y2="489" stroke="#ccd3d8"/>',
        '<text x="16" y="510" fill="#45545f" font-family="Arial,sans-serif" font-size="15">Only these fixed source models were tested.</text>',
        '</svg>',
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = render()
    path = HERE / "comparison.svg"
    if args.check:
        assert path.read_text(encoding="utf-8") == content
        print("Mobile figure: OK")
    else:
        path.write_text(content, encoding="utf-8", newline="\n")
