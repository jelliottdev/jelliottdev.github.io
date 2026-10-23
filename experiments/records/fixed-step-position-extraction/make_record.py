"""Refresh record file hashes after final edits; does not rerun statistics."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PREFIX = "experiments/records/fixed-step-position-extraction/"


def item(path: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main() -> None:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    inputs = [PREFIX + name for name in ("plan.json", "make_plan.py", "check.py")]
    inputs += [entry["path"] for entry in plan["inputs"]]
    inputs += [f"data/pages/{page}.json" for page in plan["targets"]]
    inputs = list(dict.fromkeys(inputs))
    record = {
        "id": "fixed-step-position-extraction",
        "status": "draft",
        "title": "Reading every nth rune",
        "question": "Does any fixed step from 2 to 29, with any starting phase and either page-local or joined position counting, produce English-like LP2 text?",
        "reader_question": "Has taking every nth rune at different starting points been tried?",
        "summary": "A complete 868-setting fixed-step search found no output that stood out against matched full searches on shuffled pages.",
        "finding": "The best setting was step 24, zero-based phase 2 with page resets: score −7.151 over 563 selected runes. In 182 of 256 shared page-shuffle full searches, the best setting scored at least as high (global add-one 183/257≈0.712).",
        "limitations": "Only forward steps 2–29, both stated page clocks and direct English scoring are covered. A cipher layer, other language, reversed order, alternate period range or rule chosen from page artwork remains untested. The catalog is an idea list, not evidence of a particular historical search.",
        "next_steps": "A narrower fixed-step proposal should predeclare its period/phase/boundary rule and any post-selection decoding, then predict a continuous, independently checkable reading.",
        "outcome": "not-supported",
        "tags": ["every nth rune", "fixed step", "phase search", "positional extraction", "GP29", "English scorer", "search space"],
        "related": ["line-initial-layout-control", "english-scorer-controls"],
        "scope": {
            "pages": plan["targets"],
            "artifacts": [PREFIX + "plan.json", "research/source-archive/lp2-collected-solution-ideas-2026-10-23.txt"],
            "representation": "All 12,956 canonical GP runes from the 55 rune-bearing LP2-00–55 pages; punctuation and artwork excluded.",
            "procedure": "For p=2..29 and every residue phase, select forward rune positions under page-reset or joined-book clocks. Pool within-page quadgram sums for reset cases, score joined cases as one stream. Compare the largest of 868 English scores to 256 maxima from shared within-page-shuffle full-grid searches. Plant the known GP readings into each selected stream as a sensitivity control.",
            "parameters": "868 settings (2 clocks × sum of p for p=2..29); all have ≥360 Latin quadgrams against a frozen 100-quad eligibility gate. Shared null seeds 33017121–33017376. Source-backed bound p≤29 uses GP alphabet size, without treating it as a detected period.",
            "exclusions": "Periods greater than 29, backward selection, adjustable page order, inferred or interrupted clocks, number-derived keys, further cipher layers, non-English texts and claims that this grid represents every historical attempt."
        },
        "review": {"reviewer": "Independent page-JSON and four-character ring scorer full-grid replay; 868 planted known-reading controls", "retested_on": "2026-10-23", "kind": "computational", "human_review": "pending"},
        "reproduction": {
            "command": "python experiments/records/fixed-step-position-extraction/run.py --check && python experiments/records/fixed-step-position-extraction/check.py",
            "environment": "Python 3 with NumPy and Numba; offline from repository root or extracted experiment ZIP.",
            "script": PREFIX + "run.py",
            "script_sha256": item(PREFIX + "run.py")["sha256"],
            "inputs": [item(path) for path in inputs],
            "outputs": [item(PREFIX + name) for name in ("results.json", "streams.tsv", "full-search-scores.svg")]
        },
        "sources": [
            {"label": "User-supplied solution-idea catalog, item 9.7", "url": "https://github.com/jelliottdev/jelliottdev.github.io/blob/main/research/source-archive/lp2-collected-solution-ideas-2026-10-23.txt"},
            {"label": "CicadaSolvers manuscript transcription repository", "url": "https://github.com/CicadaSolvers/CicadaSolvers.github.io"},
            {"label": "English scorer calibration", "url": "https://jelliottdev.github.io/#/experiments/english-scorer-controls"}
        ],
        "visuals": [{"path": PREFIX + "full-search-scores.svg", "caption": "The strongest observed setting lies below the median maximum of 256 complete 868-setting shuffled searches."}]
    }
    (HERE / "record.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
