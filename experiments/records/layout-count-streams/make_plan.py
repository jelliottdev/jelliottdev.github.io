"""Freeze direct GP readings of archived line and word lengths."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def pinned(path: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main() -> None:
    pages = [f"lp2-{i:02}" for i in range(56) if i != 50]
    plan = {
        "schema": "liberpedia-layout-count-streams-plan-v1",
        "frozen_before_scoring": "2026-10-23",
        "source_idea": "research/source-archive/lp2-collected-solution-ideas-2026-10-23.txt, item 9.10. This lists possible count streams, not a documented previous attempt.",
        "question": "Do the ordered counts of runes per physical line or per visible word slot behave as direct English text when interpreted as GP indices?",
        "input_rules": {
            "line-runes": "On each archived page, split the UTF-8 text on physical newlines; count only canonical GP runes in each nonempty rune-bearing line, retaining order. Empty decoration-only lines contribute no count.",
            "word-runes": "Within each page, remove slash layout marks and newlines, split on hyphens, and count canonical GP runes in each nonempty rune-bearing slot. Other punctuation is ignored. This is the visible-word convention used by the pinned rail-fence record."
        },
        "mappings": {
            "count": "Map count n to GP index n modulo 29; index zero requires count 29 in synthetic controls.",
            "count-minus-one": "Map count n to GP index n−1 modulo 29; index zero requires count 1 in synthetic controls."
        },
        "boundaries": {
            "page-local": "Translate and score each page's count stream separately, pooling English quadgram sums and counts without groups across page boundaries.",
            "joined": "Concatenate page count streams in manuscript order; translate and score as one uninterrupted stream."
        },
        "arms": [f"{source}-{mapping}-{boundary}" for source in ("line-runes", "word-runes") for mapping in ("count", "count-minus-one") for boundary in ("page-local", "joined")],
        "score": "Mean base-10 log likelihood of overlapping four-letter groups after translating GP indices to canonical Latin labels, with pinned english_quadgrams.txt and unseen count 0.01. Eligibility requires at least 100 within-segment Latin quadgrams; report a shorter arm as underpowered. No English words are selected after scoring.",
        "null": "For each of 256 trials, Python Random(33017125 + t) shuffles the observed line counts and word counts separately within every page exactly once, preserving each page's count histogram and number of events. Reuse both shared shuffled count arrays across all eight mappings/boundaries. Retain the global best eligible arm per trial.",
        "positive_control": "For each arm, create a synthetic count stream of exactly the observed page/event lengths, inverse-map successive known GP reading indices to positive counts (cycling the established source if needed), and require exact index recovery plus English score above −5.5. This validates parsing-to-index/scoring only; synthetic counts do not model typesetting.",
        "decision": "Compare the best observed eligible arm against the best of the same eight-arm search in every matched trial. A count signal may depend on another numeral system or cipher layer, so lack of direct English is not generic exclusion.",
        "targets": pages,
        "source_reading_ids": ["warning", "welcome", "some-wisdom", "first-koan", "loss-of-divinity", "second-koan", "instruction", "lp2-57"],
        "model": "experiments/records/english-scorer-controls/english_quadgrams.txt",
        "inputs": [pinned(path) for path in ["data/index.json", "data/evidence/known-readings.json", "research/source-archive/lp2-collected-solution-ideas-2026-10-23.txt", "experiments/records/english-scorer-controls/english_quadgrams.txt", *[f"text/{page}.txt" for page in pages]]]
    }
    HERE.mkdir(parents=True, exist_ok=True)
    (HERE / "plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
