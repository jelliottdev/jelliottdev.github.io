"""Freeze p=2..29, every residue and both page-boundary conventions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def pinned(path: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main() -> None:
    pages = [f"lp2-{index:02}" for index in range(56) if index != 50]
    plan = {
        "schema": "liberpedia-fixed-step-extraction-plan-v1",
        "frozen_before_scoring": "2026-10-23",
        "source_idea": "research/source-archive/lp2-collected-solution-ideas-2026-10-23.txt, item 9.7; the catalog is an idea list, not a verified prior attempt.",
        "question": "Does any fixed every-n rune selection with a declared phase produce unusually English-like text under page-local or joined indexing?",
        "representation": "Canonical rune-bearing GP29 characters in numerical LP2-00–55 page order, with empty LP2-50 excluded. Punctuation, separators and artwork do not advance the position counter.",
        "periods": "Every integer p=2..29 inclusive; 29 is the canonical GP alphabet size and is a bound, not an inferred key period.",
        "phases": "All residues r=0..p-1; select zero-based rune positions i with i mod p = r, in increasing order.",
        "boundaries": {
            "page-local": "Restart position zero on each of 55 pages; score each selected page segment without quadgrams crossing page boundaries, then pool log likelihood sums and counts.",
            "joined": "Concatenate page rune sequences with no advancing separator; run one counter and score the selected stream as one segment."
        },
        "case_count": 868,
        "scoring": "Mean base-10 log likelihood of overlapping four-letter groups after translating selected GP indices to canonical Latin labels (data/index.json); pinned english_quadgrams.txt, unseen count 0.01. A case must provide at least 100 within-segment Latin quadgrams. Eligibility is determined before output comparison; all 868 cases clear this gate by length-only audit (minimum 360 quadgrams).",
        "null": "256 trials; for trial t shuffle each of the 55 complete pages once with Python Random(33017121+t), then reuse those same shuffled pages in all 868 cases. Preserve per-page GP histograms and page boundaries. Record the maximum across all 868 scores for every trial, not individual attractive phase scores.",
        "positive_control": "For each case, fill a synthetic page-length-matched GP29 corpus with seeded random indices, overwrite its selected positions with the eight established GP reading indices repeated cyclically, verify exact extraction and score above the fixed −5.5 English-recognition threshold. This tests the extraction and scorer, not an LP2 reading.",
        "decision": "Compare the highest observed eligible case to the global maximum in each shared trial. Report all case scores and exact extracted rune/Latin streams, but do not treat 868 settings as distinct historical ideas or claim exclusion of other periods, negative directions, cipher layers or languages.",
        "targets": pages,
        "model": "experiments/records/english-scorer-controls/english_quadgrams.txt",
        "source_reading_ids": ["warning", "welcome", "some-wisdom", "first-koan", "loss-of-divinity", "second-koan", "instruction", "lp2-57"],
        "inputs": [pinned(path) for path in ["data/index.json", "data/evidence/known-readings.json", "research/source-archive/lp2-collected-solution-ideas-2026-10-23.txt", "experiments/records/english-scorer-controls/english_quadgrams.txt", *[f"text/{page}.txt" for page in pages]]]
    }
    HERE.mkdir(parents=True, exist_ok=True)
    (HERE / "plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
