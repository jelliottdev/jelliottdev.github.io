"""Small responsive matrix of Stage X4 complete-stream decoder results."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAMES = ("Raw DEFLATE", "zlib", "gzip", "bzip2", "LZMA")


def render() -> str:
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert result["decoder_tests"] == 20 and result["decoder_eof"] == 0
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 370" role="img" aria-labelledby="title desc" font-family="Arial, sans-serif">',
        '<title id="title">Complete-stream decompression of the printed grid</title>',
        '<desc id="desc">Five decoders were run on four complete grid routes. None reached end of a compressed stream. Source calibration found 552 random EOF cases in 100,000 raw DEFLATE trials and zero in the other decoder samples.</desc>',
        '<rect width="340" height="370" fill="#f6f7f8"/>',
        '<text x="16" y="30" fill="#192832" font-size="17" font-weight="700">Can the grid decompress?</text>',
        '<text x="16" y="53" fill="#45545f" font-size="14">Complete 256-byte streams; no offsets</text>',
        '<line x1="16" y1="69" x2="324" y2="69" stroke="#cbd4d9"/>',
        '<text x="146" y="93" text-anchor="middle" fill="#45545f" font-size="13">R</text>',
        '<text x="186" y="93" text-anchor="middle" fill="#45545f" font-size="13">R←</text>',
        '<text x="226" y="93" text-anchor="middle" fill="#45545f" font-size="13">C</text>',
        '<text x="266" y="93" text-anchor="middle" fill="#45545f" font-size="13">C←</text>',
        '<text x="324" y="93" text-anchor="end" fill="#45545f" font-size="13">EOF</text>',
    ]
    for i, name in enumerate(NAMES):
        y = 124 + 36 * i
        lines.append(f'<text x="16" y="{y + 5}" fill="#263741" font-size="14">{name}</text>')
        lines.append(f'<line x1="16" y1="{y + 17}" x2="324" y2="{y + 17}" stroke="#e1e5e8"/>')
        for x in (146, 186, 226, 266):
            lines.append(f'<circle cx="{x}" cy="{y}" r="6" fill="#f6f7f8" stroke="#648294" stroke-width="2"/>')
        lines.append(f'<text x="324" y="{y + 5}" text-anchor="end" fill="#263741" font-size="14" font-weight="700">0/4</text>')
    lines += [
        '<text x="16" y="319" fill="#45545f" font-size="13">Open circle: decoder did not reach EOF.</text>',
        '<text x="16" y="344" fill="#45545f" font-size="13">Random EOFs: raw DEFLATE 552 / 100,000;</text>',
        '<text x="16" y="361" fill="#45545f" font-size="13">other sampled decoders 0 / 100,000 each.</text>',
        '</svg>',
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = render()
    path = HERE / "decoder-screen.svg"
    if args.check:
        assert path.read_text(encoding="utf-8") == content
        print("Stage X4 decoder chart: OK")
    else:
        path.write_text(content, encoding="utf-8", newline="\n")
