"""Freeze draft publication metadata after rerun and independent check."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PREFIX = "experiments/records/lp2-row-column-english"
plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))


def pin(path: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


record = {
    "id": "lp2-row-column-english",
    "status": "draft",
    "title": "Do simple row or column routes reveal text?",
    "question": "Does any complete archived-row or ordinal-column route make a whole LP2 page English-like without changing rune values?",
    "reader_question": "Have we tried reading the full pages by rows and columns?",
    "summary": "A complete 16-route-per-page English-score search has a modestly high best score but no readable passage; the full-grid shuffle comparison is not decisive.",
    "finding": "LP2-22 read down ordinal columns from right to left scores −6.890 over 131 runes. In 16 of 256 matched complete-route shuffled searches, the best eligible route scored at least as high (global add-one 17/257≈0.066). The output begins WRRJJTMUXW… and is not a decipherment.",
    "limitations": "Only the archived left-aligned, ragged ordinal row/column rules and direct English scoring were tested. Physical image columns, diagonals, spirals, additional cipher layers and other languages remain open; the catalog does not verify a prior historical run. The null adjusts the 880-setting route search, not earlier selection of this family among many ideas.",
    "next_steps": "A more specific route proposal should specify its source-image geometry or row convention before outcome inspection and predict a continuous reading that transfers to another section.",
    "outcome": "inconclusive",
    "tags": ["row route", "column route", "pure transposition", "ordinal columns", "GP29", "English scorer", "search space"],
    "related": ["lp2-row-column-routes", "rail-fence-visible-words", "english-scorer-controls"],
    "scope": {
        "pages": plan["targets"],
        "artifacts": [f"{PREFIX}/plan.json", "experiments/records/lp2-row-column-routes/results.json",
                      "research/source-archive/lp2-collected-solution-ideas-2026-10-23.txt"],
        "representation": "All 55 rune-bearing LP2-00–55 text pages as ragged, left-aligned source rows. The pinned 16-route trace is reused by the producer and rebuilt from structured page JSON by the checker.",
        "procedure": "Score the full output of 16 pure row/column routes per page with canonical GP Latin quadgrams; compare the best eligible route with 256 maxima of complete 880-route searches on shared within-page rune shuffles.",
        "parameters": "880 parameter routes, 848 with ≥100 English quadgrams; 256 shared full-route controls seeded 33017128–33017383; all 16 routes have exact inverse-permutation planted Welcome-reading controls.",
        "exclusions": "Physical image alignment, diagonals, rectangle padding, spirals, arbitrary permutations, across-page transposition, added substitutions, non-English output and claims about all historical attempts."
    },
    "review": {
        "reviewer": "Independent page-JSON route and scoring full-grid reconstruction; 16 inverse-permutation planted controls",
        "retested_on": "2026-10-23",
        "kind": "computational",
        "human_review": "pending"
    },
    "reproduction": {
        "command": f"python {PREFIX}/run.py --check && python {PREFIX}/check.py",
        "environment": "Python 3, NumPy and Numba; offline from repository root or extracted experiment ZIP.",
        "script": f"{PREFIX}/run.py",
        "script_sha256": pin(f"{PREFIX}/run.py")["sha256"],
        "inputs": [pin(f"{PREFIX}/{name}") for name in ("plan.json", "make_plan.py", "check.py", "make_record.py")]
                  + [pin(row["path"]) for row in plan["inputs"]]
                  + [pin(f"data/pages/{page}.json") for page in plan["targets"]],
        "outputs": [pin(f"{PREFIX}/{name}") for name in ("results.json", "route-scores.svg")]
    },
    "sources": [
        {"label": "User-supplied solution-idea catalog, item 9.2", "url": "https://github.com/jelliottdev/jelliottdev.github.io/blob/main/research/source-archive/lp2-collected-solution-ideas-2026-10-23.txt"},
        {"label": "Earlier exact row/column route experiment", "url": "https://jelliottdev.github.io/#/experiments/lp2-row-column-routes"},
        {"label": "CicadaSolvers manuscript transcription repository", "url": "https://github.com/CicadaSolvers/CicadaSolvers.github.io"}
    ],
    "visuals": [{"path": f"{PREFIX}/route-scores.svg", "caption": "The leading LP2-22 ordinal-column route and its score in the complete-route shuffled-search distribution."}]
}

(HERE / "record.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
