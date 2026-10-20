"""Plot the saved descriptive audit. Requires matplotlib; no network calls."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    parser.error("Output already exists")
data = json.loads((ROOT / "exports/gap-file-sizes.json").read_text(encoding="utf-8"))
plt.rcParams.update({"font.size": 12, "svg.fonttype": "none", "svg.hashsalt": "liberpedia-gap-sizes"})
fig, ax = plt.subplots(figsize=(4.8, 5.2))
for group, label, marker, color in [
    ("gap", "Reported gap (16)", "o", "#245d75"),
    ("comparison", "Comparison (15)", "s", "#9c571d"),
    ("unlisted", "Unlisted (27)", "x", "#666666"),
]:
    rows = [r for r in data["files"] if r["reported_group"] == group]
    ax.scatter([int(r["page"].split("-")[1]) for r in rows],
               [r["bytes"] / 1024 for r in rows], label=label,
               marker=marker, color=color, s=38)
ax.set(xlabel="LP2 page number", ylabel="Original JPEG size (KiB)",
       xlim=(-1, 58), ylim=(0, 850), xticks=[0, 10, 20, 30, 40, 50, 57])
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", alpha=.2)
ax.set_axisbelow(True)
ax.legend(loc="upper left", frameon=False, fontsize=11)
fig.tight_layout()
fig.savefig(args.output, metadata={"Date": None})
