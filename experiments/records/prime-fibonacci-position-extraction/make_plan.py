"""Freeze the four page-boundary/position-selector arms before scoring."""
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
        "schema": "liberpedia-prime-fibonacci-extraction-plan-v1",
        "frozen_before_scoring": "2026-10-23",
        "source_idea": "research/source-archive/lp2-collected-solution-ideas-2026-10-23.txt, item 9.7. This catalogs possible extraction methods, not a documented historical solve attempt.",
        "question": "Do prime- or Fibonacci-indexed GP runes read as English more strongly than equal-length fixed-position selections from per-page shuffled controls?",
        "representation": "Canonical GP29 rune-bearing characters in each LP2-00–55 text file, including headers; exclude punctuation and layout. LP2-50 has no runes and is excluded. Pages retain numerical order.",
        "selectors": {
            "prime": "One-based prime positions 2,3,5,7,... up to length, increasing order.",
            "fibonacci": "One-based unique Fibonacci positions 1,2,3,5,8,... up to length, increasing order; the repeated 1 is selected once."
        },
        "boundaries": {
            "page-local": "Restart the index at each of 55 page starts; score each selected page segment separately and pool log quadgram sums/counts, never adding a quadgram across page boundaries.",
            "joined": "Concatenate the 55 rune streams with no advancing separator, then index once over the entire joined stream and score the selected stream."
        },
        "arms": ["prime-page-local", "prime-joined", "fibonacci-page-local", "fibonacci-joined"],
        "score": "Mean base-10 English quadgram log likelihood on concatenated canonical GP Latin labels within each selected segment, using the pinned english_quadgrams.txt with unseen count 0.01. Score an arm only when it supplies at least 100 within-segment Latin quadgrams; report shorter arms as underpowered rather than negative.",
        "null": "For each of 256 trials, seeded Python Random(33017119 + trial), shuffle every complete page independently once, preserving each page's GP histogram. Reuse the same 55 shuffled pages for every arm; rerun the fixed selectors and boundaries. Record each arm and the largest score across eligible arms per trial. No adaptive selector or phase choices.",
        "positive_control": "For each eligible arm, create synthetic pages of matching lengths. Put consecutive GP indices from warning, welcome, some-wisdom, first-koan, loss-of-divinity, second-koan, instruction and lp2-57 into that arm's selected positions; exclude lp2-56. Fill all other positions with seeded uniform GP indices, and require exact extraction of planted indices and higher score than the same-arm median null. The control checks extraction and scorer, not LP2 decipherment.",
        "decision": "Compare the strongest eligible observed arm with the global maximum in each shared null trial. Preserve per-arm score and quadgram count; no claim about short unscored streams, hidden encodings, alternative extraction origins or any generic prime/Fibonacci family.",
        "targets": pages,
        "model": "experiments/records/english-scorer-controls/english_quadgrams.txt",
        "inputs": [pinned(path) for path in ["data/index.json", "data/evidence/known-readings.json", "research/source-archive/lp2-collected-solution-ideas-2026-10-23.txt", "experiments/records/english-scorer-controls/english_quadgrams.txt", *[f"text/{page}.txt" for page in pages]]],
    }
    HERE.mkdir(parents=True, exist_ok=True)
    (HERE / "plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
