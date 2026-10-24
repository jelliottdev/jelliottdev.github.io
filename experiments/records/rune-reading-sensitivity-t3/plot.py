"""Render a narrow-screen comparison of the exact 450-change result."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def make_svg():
    r = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    rows = [
        ("Stored runes", r["baseline"]["doublets"], "#6e8490"),
        ("450 hypothetical changes", r["all_450_source_alternatives"]["doublets"], "#285b78"),
        ("Source German comparison", r["source_german_comparison_floor_doublets"], "#929da5"),
    ]
    maxval = 140
    marks = []
    for idx, (label, value, color) in enumerate(rows):
        y = 83 + idx * 61
        width = value / maxval * 246
        marks.append(f'<text x="20" y="{y}" font-size="14" fill="#24313a">{label}</text>')
        marks.append(f'<rect x="20" y="{y+10}" width="{width:.2f}" height="14" rx="2" fill="{color}"/>')
        marks.append(f'<text x="{min(322, 28+width):.2f}" y="{y+22}" font-size="14" fill="#24313a">{value}</text>')
    return ("<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 340 276\" role=\"img\" "
            "aria-labelledby=\"title desc\">\n"
            "<title id=\"title\">Adjacent rune repeats after changing 450 disputed readings</title>\n"
            "<desc id=\"desc\">The stored stream has 86 adjacent repeats. Replacing all 450 O/A/AE "
            "machine disagreements with the source alternatives gives 103. A German comparison floor "
            "used by the source corresponds to 126. These alternatives are not verified corrections.</desc>\n"
            "<rect width=\"340\" height=\"276\" fill=\"#f3f5f6\"/>\n"
            "<text x=\"20\" y=\"30\" font-family=\"Arial,sans-serif\" font-size=\"17\" "
            "font-weight=\"700\" fill=\"#1f303b\">Adjacent rune repeats</text>\n"
            "<text x=\"20\" y=\"51\" font-family=\"Arial,sans-serif\" font-size=\"13\" "
            "fill=\"#52636e\">12,956 runes · one conditional comparison</text>\n"
            "<g font-family=\"Arial,sans-serif\">\n" + "\n".join(marks) + "\n</g>\n"
            "<text x=\"20\" y=\"260\" font-family=\"Arial,sans-serif\" font-size=\"13\" "
            "fill=\"#52636e\">450 changes: +17 repeats. Floor: +40.</text>\n</svg>\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    path = HERE / "comparison.svg"
    text = make_svg()
    if args.check:
        assert path.read_text(encoding="utf-8") == text
        print("PASS: comparison.svg matches the exact saved counts")
    else:
        path.write_text(text, encoding="utf-8", newline="\n")
        print(path)
