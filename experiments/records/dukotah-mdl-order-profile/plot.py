"""Draw the mobile first-order entropy comparison from frozen results."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def make():
    source = json.loads((HERE / "source-mdl_result.json").read_text(encoding="utf-8"))
    diagnostic = json.loads((HERE / "diagnostic-results.json").read_text(encoding="utf-8"))
    iid = source["entropy_rate"]["1"]
    same = diagnostic["summaries"]["order1"]
    observed = diagnostic["real"]["order1"]
    x = lambda v: 20 + (v - 4.78) / .04 * 280
    lo, hi = same["control_central95"]
    # Source stores mean and SD, not every iid control; use a labeled mean
    # marker rather than fabricating a central interval.
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 260" role="img" aria-labelledby="title desc" style="font-family:Arial,sans-serif">
<title id="title">Where the first-order entropy sits</title>
<desc id="desc">The manuscript is far below the original independent controls. It lies inside the central range of controls matched to its 86 adjacent repeats.</desc>
<rect width="320" height="260" fill="#f4f6f7"/>
<text x="18" y="29" font-size="17" font-weight="700" fill="#202b32">A smaller gap after matching repeats</text>
<text x="18" y="55" font-size="13" fill="#45545d">Conditional entropy, bits per rune</text>
<text x="18" y="87" font-size="14" fill="#24353e">Manuscript</text>
<circle cx="{x(observed):.1f}" cy="102" r="7" fill="#1d5d79"/>
<text x="{x(observed)+11:.1f}" y="107" font-size="13" fill="#24353e">{observed:.4f}</text>
<text x="18" y="136" font-size="14" fill="#24353e">40 independent controls</text>
<circle cx="{x(iid['ctrl_mean']):.1f}" cy="151" r="7" fill="#85949d"/>
<text x="{x(iid['ctrl_mean'])-2:.1f}" y="174" text-anchor="middle" font-size="13" fill="#45545d">{iid['ctrl_mean']:.4f}</text>
<text x="18" y="198" font-size="14" fill="#24353e">1,000 same-repeat controls</text>
<line x1="{x(lo):.1f}" x2="{x(hi):.1f}" y1="217" y2="217" stroke="#1d5d79" stroke-width="9" stroke-linecap="round"/>
<circle cx="{x(observed):.1f}" cy="217" r="5" fill="#fff" stroke="#1d5d79" stroke-width="2"/>
<text x="18" y="246" font-size="13" fill="#45545d">Range: {lo:.4f}–{hi:.4f}; manuscript inside</text>
</svg>'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = HERE / "order-one-controls.svg"
    content = make()
    if args.check:
        assert target.read_text(encoding="utf-8") == content
        print("PASS: SVG matches frozen numbers")
    else:
        target.write_text(content, encoding="utf-8", newline="\n")
        print(hashlib.sha256(target.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
