"""Check the method guide's displayed choice rows against its archived data."""

import json
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ChoiceRows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.variant = None
        self.cell = None
        self.current_row = None
        self.rows = {"fixed": [], "zero-shift": []}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "tbody" and attrs.get("data-variant") in self.rows:
            self.variant = attrs["data-variant"]
        elif self.variant and tag == "tr":
            self.current_row = []
        elif self.current_row is not None and tag in {"th", "td"}:
            self.cell = ""

    def handle_data(self, data):
        if self.cell is not None:
            self.cell += data

    def handle_endtag(self, tag):
        if tag in {"th", "td"} and self.cell is not None:
            self.current_row.append(self.cell.strip())
            self.cell = None
        elif tag == "tr" and self.current_row is not None:
            self.rows[self.variant].append(self.current_row)
            self.current_row = None
        elif tag == "tbody" and self.variant:
            self.variant = None


def expected_rows(rows):
    signs = {-1: "−", 1: "+"}
    return [
        [" ".join(signs[value] for value in row["signs"]),
         ", ".join(str(value) for value in row["output"])]
        for row in rows
    ]


def main():
    data = json.loads((ROOT / "exports/switching-choices-example.json").read_text(encoding="utf-8"))
    html = (ROOT / "articles/method-adaptive-rules.html").read_text(encoding="utf-8")
    parser = ChoiceRows()
    parser.feed(html)
    assert parser.rows["fixed"] == expected_rows(data["rows"]), "Fixed-shift rows differ from JSON"
    comparison = data["zero_shift_comparison"]
    assert parser.rows["zero-shift"] == expected_rows(comparison["rows"]), "Zero-shift rows differ from JSON"
    assert len(parser.rows["fixed"]) == data["configurations"]
    assert len({tuple(row["output"]) for row in data["rows"]}) == data["distinct_outputs"]
    assert len(parser.rows["zero-shift"]) == comparison["configurations"]
    assert len({tuple(row["output"]) for row in comparison["rows"]}) == comparison["distinct_outputs"]
    assert "exports/figures/switching-choices-example.svg" in html
    print("PASS: both displayed choice tables match the archived JSON")


if __name__ == "__main__":
    main()
