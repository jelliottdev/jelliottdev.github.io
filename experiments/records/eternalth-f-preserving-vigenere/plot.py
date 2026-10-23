"""Small source-rule diagram and result summary, readable at phone width."""
import argparse
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
RESULT = json.loads((HERE / "results.json").read_text(encoding="utf-8"))


def make_svg():
    impossible = RESULT["page_count"] - len(RESULT["f_possible_pages"])
    shuffles = RESULT["null_at_least_best"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 308" role="img" aria-labelledby="title desc">
<title id="title">Fixed key with and without preserved F</title>
<desc id="desc">At key slot I, both F and X become F, making N impossible. The observed full pages violate this rule on {impossible} of 55 pages. The ordinary inverse has no English-scoring page; {shuffles} of 199 shuffled searches scored at least as high as its best page.</desc>
<rect width="340" height="308" fill="#f7f9fa"/>
<text x="16" y="27" fill="#172b39" font-family="Arial,sans-serif" font-size="17" font-weight="700">The F rule has a missing output</text>
<text x="16" y="52" fill="#425560" font-family="Arial,sans-serif" font-size="13">At the key's second letter, I = 8:</text>
<rect x="16" y="66" width="308" height="66" rx="4" fill="#e9eff3"/>
<text x="30" y="91" fill="#173f56" font-family="Arial,sans-serif" font-size="17" font-weight="700">F  →  F</text>
<text x="170" y="91" fill="#173f56" font-family="Arial,sans-serif" font-size="17" font-weight="700">X  →  F</text>
<text x="30" y="118" fill="#425560" font-family="Arial,sans-serif" font-size="13">N cannot appear in this slot.</text>
<text x="16" y="159" fill="#172b39" font-family="Arial,sans-serif" font-size="16" font-weight="700">Literal F-preserving encoder</text>
<rect x="16" y="172" width="296" height="19" rx="2" fill="#d9e0e4"/>
<rect x="16" y="172" width="285" height="19" rx="2" fill="#2b5c79"/>
<text x="16" y="212" fill="#172b39" font-family="Arial,sans-serif" font-size="14">{impossible} of 55 pages contain a forbidden letter.</text>
<text x="16" y="234" fill="#425560" font-family="Arial,sans-serif" font-size="13">Two pages pass this necessary condition.</text>
<line x1="16" y1="249" x2="324" y2="249" stroke="#c8d1d7"/>
<text x="16" y="272" fill="#172b39" font-family="Arial,sans-serif" font-size="15" font-weight="700">Ordinary Vigenère branch</text>
<text x="16" y="294" fill="#425560" font-family="Arial,sans-serif" font-size="13">{shuffles}/199 controls scored as well or higher.</text>
</svg>'''


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = HERE / "summary.svg"
    expected = make_svg()
    if args.check:
        assert path.read_text(encoding="utf-8") == expected
        print("Phone-width source-rule figure matches saved results")
    else:
        path.write_text(expected, encoding="utf-8", newline="\n")
        print(path)
