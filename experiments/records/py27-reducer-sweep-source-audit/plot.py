"""Draw the source pipeline and the control-path omission."""
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render() -> str:
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 620 430" role="img" aria-labelledby="t d">
<title id="t">Screening gate absent from the published positive control</title>
<desc id="d">The real sweep routes every candidate through a 120-rune screen and promotes it at pmax five before the full 240-rune test. The planted control goes directly to the full test, leaving screen recall unchecked.</desc>
<rect width="620" height="430" fill="#f5f6f7"/>
<text x="24" y="37" font-size="22" font-family="Arial,sans-serif" font-weight="700" fill="#202a31">What the control checks</text>
<text x="24" y="78" font-size="16" font-family="Arial,sans-serif" font-weight="700" fill="#335466">Actual source sweep</text>
<rect x="24" y="93" width="572" height="61" rx="4" fill="#fff" stroke="#aab7be"/>
<text x="40" y="118" font-size="16" font-family="Arial,sans-serif" fill="#202a31">Stage A · first 120 runes · beam width 64</text>
<text x="40" y="141" font-size="14" font-family="Arial,sans-serif" fill="#52616a">Promote when panel score ≥ 5.0</text>
<path d="M310 154v28" stroke="#335466" stroke-width="2"/><path d="m304 176 6 7 6-7" fill="none" stroke="#335466" stroke-width="2"/>
<rect x="24" y="184" width="572" height="62" rx="4" fill="#fff" stroke="#aab7be"/>
<text x="40" y="209" font-size="16" font-family="Arial,sans-serif" fill="#202a31">Stage B · full 240 runes · final hit gate</text>
<text x="40" y="231" font-size="14" font-family="Arial,sans-serif" fill="#52616a">95 saved Stage-B rows; none clears 7.634</text>
<line x1="24" y1="270" x2="596" y2="270" stroke="#cbd3d8"/>
<text x="24" y="304" font-size="16" font-family="Arial,sans-serif" font-weight="700" fill="#335466">Published planted-key control</text>
<rect x="24" y="320" width="572" height="63" rx="4" fill="#fff" stroke="#aab7be"/>
<text x="40" y="346" font-size="16" font-family="Arial,sans-serif" fill="#202a31">Direct full 240-rune evaluation · 4/4 pass</text>
<text x="40" y="369" font-size="14" font-family="Arial,sans-serif" fill="#52616a">No Stage-A score or promotion test is recorded</text>
<text x="24" y="413" font-size="13" font-family="Arial,sans-serif" fill="#52616a">Source-path audit; this diagram does not rerun the missing trained model.</text>
</svg>'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = HERE / "screen-control-gap.svg"
    if args.check:
        assert path.read_text(encoding="utf-8") == render()
        print("PASS: diagram matches generator")
    else:
        path.write_text(render(), encoding="utf-8", newline="\n")
        print("Wrote", path)


if __name__ == "__main__":
    main()
