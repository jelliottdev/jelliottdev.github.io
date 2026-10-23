"""Independent source-input and mathematical checks; does not import run.py."""
import itertools
import json
import math
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SYMS = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
MAP = {c: i for i, c in enumerate(SYMS)}


def main():
    out = json.loads((HERE/"results.json").read_text(encoding="utf-8"))
    raw = (HERE/"source"/"krisyotam_runes.txt").read_text(encoding="utf-8")
    # Independent tokenization: page/line/word/sentence breaks terminate runs.
    pages = raw.split("%")[:55]
    all_runs = []
    for page in pages:
        for chunk in re.split(r"[-./\n]+", page):
            vals = [MAP[c] for c in chunk if c in MAP]
            if vals:
                all_runs.append(vals)
    # Source treats a newline before a hyphen as a line boundary too.
    counts = Counter((y-x) % 29 for row in all_runs for x, y in zip(row, row[1:]))
    assert len(all_runs) == out["runs"]
    assert sum(counts.values()) == out["adjacent_pairs"] == 9640
    assert counts[0] == out["d0_doublets"] == 60
    vals = [counts[i] for i in range(1, 29)]
    assert vals == out["baseline"]["nonzero_counts"]
    mu = sum(vals)/28
    cv = math.sqrt(sum((v-mu)**2 for v in vals)/28)/mu
    chi = sum((v-mu)**2/mu for v in vals)
    assert math.isclose(cv, out["baseline"]["cv"], abs_tol=1e-12)
    assert math.isclose(chi, out["baseline"]["chi"], abs_tol=1e-10)
    # Exact free-diagonal maximum: all additions to the largest original bin.
    peak = max(vals)
    original_squares = sum(v*v for v in vals)
    total = sum(vals)
    for row in out["sweep"]:
        k = row["k"]
        mean = (total+k)/28
        squares = original_squares - peak*peak + (peak+k)**2
        upper = math.sqrt(squares/28 - mean*mean)/mean
        assert math.isclose(upper, row["free_diagonal_upper_cv"], abs_tol=1e-12)
        assert math.isclose(cv, row["physical_cv"], abs_tol=1e-12)
    # Exhaustive local algebra check for duplicate insertion across every rune triple.
    for a, x, b in itertools.product(range(29), repeat=3):
        before = Counter(((x-a)%29, (b-x)%29))
        after = Counter(((x-a)%29, 0, (b-x)%29))
        assert after-before == Counter({0:1})
    control = out["synthetic_control"]
    assert control["autokey_merges"] == control["uniform_merges"] == 20
    assert control["autokey_after_20"] >= .3
    assert control["uniform_after_20"] < .15
    assert control["separation_after"] >= .15
    assert out["sweep"][20]["free_diagonal_upper_cv"] < .3
    assert out["sweep"][40]["free_diagonal_upper_cv"] < .3
    print("Independent parser, 41 exact bounds, 24,389 insertion triples and planted-control gates pass.")


if __name__ == "__main__":
    main()
