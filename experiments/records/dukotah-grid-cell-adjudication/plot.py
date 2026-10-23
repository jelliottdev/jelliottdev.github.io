"""Make a compact source-pixel comparison from the three exact JPEGs."""
from __future__ import annotations

import base64
import io
import json
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = json.loads((HERE / "replay-plan.json").read_text(encoding="utf-8"))
GRID = json.loads((HERE / "replay-output/grid.json").read_text(encoding="utf-8"))
ADJ = json.loads((HERE / "replay-output/adjudication.json").read_text(encoding="utf-8"))


def main():
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="350" height="590" viewBox="0 0 350 590" role="img" aria-label="Six disputed grid cells: original image crop, reproduced token and competing decimal-column value">',
             '<rect width="350" height="590" fill="#fff"/>',
             '<g font-family="Arial,sans-serif" fill="#20272c">',
             '<text x="12" y="26" font-size="18" font-weight="700">Six disputed cells</text>',
             '<text x="12" y="48" font-size="13" fill="#53616b">Original pixel crop → token → byte</text>']
    for k, idx in enumerate(PLAN["fixed_contested_indices"]):
        if idx < 80: page, j = 49, idx
        elif idx < 184: page, j = 50, idx - 80
        else: page, j = 51, idx - 184
        b = GRID[f"p{page}"][j]
        im = Image.open(ROOT / "images" / f"lp2-{page}.jpg").convert("RGB")
        crop = im.crop(tuple(b))
        buf = io.BytesIO()
        crop.save(buf, format="PNG")
        href = base64.b64encode(buf.getvalue()).decode("ascii")
        row = ADJ[str(idx)]
        y = 66 + 85 * k
        lines.extend([
            f'<line x1="12" y1="{y+78}" x2="338" y2="{y+78}" stroke="#d5dce0"/>',
            f'<text x="12" y="{y+16}" font-size="13" fill="#53616b">Cell {idx} · LP2-{page}</text>',
            f'<rect x="12" y="{y+23}" width="78" height="48" fill="#f2f4f5" stroke="#cbd2d5"/>',
            f'<image x="19" y="{y+25}" width="64" height="44" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{href}"/>',
            f'<text x="104" y="{y+47}" font-size="20" font-weight="700">{row["token"]} → {row["byte"]}</text>',
            f'<text x="104" y="{y+68}" font-size="13" fill="#53616b">Decimal column: {row["decpref_byte"]}</text>'
        ])
    lines.append('</g></svg>')
    (HERE / "six-cells.svg").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
