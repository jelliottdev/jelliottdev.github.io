"""Render the two archived-stream frequency examples used by the IoC guide.

Requires matplotlib. Run from any directory:
    python scripts/plot_rune_frequencies.py --output my-rune-frequencies.svg
The output must not exist. This reads saved counts; rune_ioc.py --check verifies
those counts against the archived transcriptions.
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; choose a new filename.")
    report = json.loads((ROOT / "data/evidence/rune-ioc.json").read_text(encoding="utf-8"))
    records = {r["page"]: r for r in report["records"]}
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "svg.fonttype": "none", "svg.hashsalt": "liberpedia-frequency-v1"})
    fig, axes = plt.subplots(2, 1, figsize=(8, 6.5), sharex=True, sharey=True)
    for ax, pid in zip(axes, ("lp2-31", "lp2-57")):
        row = records[pid]
        assert len(row["counts"]) == 29 and sum(row["counts"]) == row["n"]
        ax.bar(range(29), [c / row["n"] for c in row["counts"]],
               width=.74, color="#365e70")
        ax.axhline(1 / 29, color="#8b5b31", linestyle="--", linewidth=1.2)
        ax.set_title(f'{pid.upper()} · {row["n"]} runes · IoC {row["ioc"]:.5f}',
                     loc="left", fontsize=13, pad=12)
        ax.set_ylim(0, .18)
        ax.set_yticks([0, .05, .10, .15])
        ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
        ax.set_ylabel("Share of runes")
        ax.grid(axis="y", color="#dddddd", linewidth=.6)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_xlim(-.7, 28.7)
    axes[-1].set_xticks(range(0, 29, 2))
    axes[-1].set_xlabel("Rune index in Gematria Primus (0–28)")
    fig.text(.12, .025, "Dashed line: 1/29 per symbol. Archived runes, including headings.\n"
             "Same axes; different text lengths. This is not a significance test.",
             fontsize=10, color="#555555")
    fig.subplots_adjust(left=.12, right=.97, top=.93, bottom=.17, hspace=.38)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as output:
        fig.savefig(output, format="svg", metadata={"Date": None,
                    "Title": "Archived rune frequencies for LP2-31 and LP2-57"})
    plt.close(fig)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
