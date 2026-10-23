"""Refresh experiment metadata hashes without rerunning results."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PREFIX = "experiments/records/prime-fibonacci-position-extraction/"


def item(path: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def make() -> None:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    files = [PREFIX + name for name in ("plan.json", "make_plan.py", "check.py")]
    files += [entry["path"] for entry in plan["inputs"]]
    files += [f"data/pages/{page}.json" for page in plan["targets"]]
    files = list(dict.fromkeys(files))
    record = {
        "id": "prime-fibonacci-position-extraction",
        "status": "draft",
        "title": "Runes at prime and Fibonacci positions",
        "question": "Do forward, one-based prime or Fibonacci rune positions yield English-like text when applied per page or across the joined LP2 pages?",
        "reader_question": "What happens if we read only the prime- or Fibonacci-numbered runes?",
        "summary": "Three long-enough direct extractions did not outperform the best of the same methods on page-preserving shuffled controls; the book-wide Fibonacci stream was too short to assess.",
        "finding": "Page-local prime extraction scored −7.472, the best of three eligible arms. In 201 of 256 page-shuffled trials, the strongest eligible arm scored at least that high (global add-one estimate 202/257≈0.786). The joined Fibonacci arm selected only 20 runes and was not scored.",
        "limitations": "Direct English quadgram scoring cannot exclude further encryption, another language or alternate position origins/directions. The book-wide Fibonacci stream is too short for the declared scorer. The catalog is an idea list, not a verified historical test record.",
        "next_steps": "Any more specific positional claim should fix index origin, page boundaries, direction and any second decoding layer before inspecting outputs, then compare its full selection search to matching controls.",
        "outcome": "not-supported",
        "tags": ["prime positions", "Fibonacci positions", "positional extraction", "GP29", "language score", "search space"],
        "related": ["line-initial-layout-control", "lp2-fibonacci-openings", "english-scorer-controls"],
        "scope": {
            "pages": plan["targets"],
            "artifacts": [PREFIX + "plan.json", "research/source-archive/lp2-collected-solution-ideas-2026-10-23.txt"],
            "representation": "12,956 recorded GP runes on the 55 rune-bearing LP2-00–55 pages, with non-rune punctuation and artwork excluded.",
            "procedure": "Select one-based prime or unique Fibonacci positions, either restarting per page and pooling within-page English quadgrams or indexing the joined page stream once. Require at least 100 Latin quadgrams to score. Compare the best eligible arm to 256 shared within-page-shuffle global maxima and verify planted known-reading extraction.",
            "parameters": "Two selectors × two boundary rules; prime-page-local 2,797 selected runes, prime-joined 1,542, Fibonacci-page-local 634, Fibonacci-joined 20 (unscored). 256 null trials with seed 33017119+trial.",
            "exclusions": "Every-n/phase variants, backwards indexing, alternate page ordering, another cipher layer, alternate languages, using selected positions as a key rather than direct text and claims about unscored short outputs."
        },
        "review": {"reviewer": "Independent page-JSON, trial-division and counted-quadgram replay with planted known-reading controls", "retested_on": "2026-10-23", "kind": "computational", "human_review": "pending"},
        "reproduction": {
            "command": "python experiments/records/prime-fibonacci-position-extraction/run.py --check && python experiments/records/prime-fibonacci-position-extraction/check.py",
            "environment": "Python 3 standard library; offline from repository root or extracted experiment ZIP.",
            "script": PREFIX + "run.py",
            "script_sha256": item(PREFIX + "run.py")["sha256"],
            "inputs": [item(path) for path in files],
            "outputs": [item(PREFIX + name) for name in ("results.json", "selection-scores.svg")]
        },
        "sources": [
            {"label": "User-supplied solution-idea catalog, item 9.7", "url": "https://github.com/jelliottdev/jelliottdev.github.io/blob/main/research/source-archive/lp2-collected-solution-ideas-2026-10-23.txt"},
            {"label": "CicadaSolvers manuscript transcription repository", "url": "https://github.com/CicadaSolvers/CicadaSolvers.github.io"},
            {"label": "English scorer controls", "url": "https://jelliottdev.github.io/#/experiments/english-scorer-controls"}
        ],
        "visuals": [{"path": PREFIX + "selection-scores.svg", "caption": "The strongest selected stream does not beat the best of a matched three-arm search in most shared page-shuffle trials."}]
    }
    (HERE / "record.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    make()
