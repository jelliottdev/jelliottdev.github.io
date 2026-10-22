"""Render a compact fixed-control histogram without external packages."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render():
    data = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    hist = {int(k): v for k, v in data["control"]["histogram"].items()}
    observed = data["observed_matching_windows"]
    width, height = 720, 340
    left, top, right, bottom = 60, 52, 18, 65
    plot_h = height - top - bottom
    keys = list(range(min(hist), max(hist) + 1))
    bar_w = (width - left - right) / len(keys)
    scale = plot_h / max(hist.values())
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
           '<title id="title">Crib-difference matches in page-shuffled controls</title>',
           f'<desc id="desc">Observed {observed} matching windows, compared with 2000 within-page shuffled sources. Control mean {data["control"]["mean_matching_windows"]:.3f}.</desc>',
           '<rect width="720" height="340" fill="#fff"/>',
           '<text x="60" y="29" fill="#182a34" font-family="Arial,sans-serif" font-size="17" font-weight="700">Matching windows across 17 fixed crib sequences</text>',
           f'<text x="60" y="47" fill="#435b68" font-family="Arial,sans-serif" font-size="11">Observed {observed}; within-page shuffle mean {data["control"]["mean_matching_windows"]:.2f}; 2,000 controls</text>',
           f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#667680"/>']
    for i, k in enumerate(keys):
        n = hist.get(k, 0)
        x = left + i * bar_w + 1
        h = n * scale
        color = "#a94d2a" if k == observed else "#698797"
        out.append(f'<rect x="{x:.2f}" y="{height-bottom-h:.2f}" width="{bar_w-2:.2f}" height="{h:.2f}" fill="{color}"/>')
        if k % 2 == 0 or k == observed:
            out.append(f'<text x="{x+bar_w/2:.2f}" y="{height-bottom+17}" text-anchor="middle" fill="#384d59" font-family="Arial,sans-serif" font-size="10">{k}</text>')
    out.append('<text x="360" y="328" text-anchor="middle" fill="#384d59" font-family="Arial,sans-serif" font-size="11">Exact three-rune matches in one full source scan</text>')
    out.append('</svg>')
    return ("\n".join(out) + "\n").encode("utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    path = HERE / "matching-windows.svg"
    output = render()
    if args.check:
        assert path.read_bytes() == output
        print("PASS: SVG reproduced")
    else:
        path.write_bytes(output)
        print(path)
