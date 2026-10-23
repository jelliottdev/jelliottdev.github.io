"""Freeze an English-reading test of the catalogued page-as-key idea."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def pinned(path: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


targets = [f"lp2-{n:02d}" for n in range(56) if n != 50]
paths = ["data/index.json", "data/evidence/known-readings.json",
         "experiments/records/english-scorer-controls/english_quadgrams.txt",
         "research/source-archive/lp2-collected-solution-ideas-2026-10-23.txt"]
paths += [f"text/{page}.txt" for page in targets]
plan = {
    "schema": "liberpedia-page-pair-english-plan-v1",
    "frozen_before_scoring": "2026-10-23",
    "source_idea": "User-supplied collected-ideas catalog item 7.3, using one LP2 ciphertext page as another's key. This is a newly bounded test, not a replay of a documented historical run.",
    "prior_overlap": "lp2-page-pair-alignment measured IoC of zero-offset sums and differences, not whether their GP-label output resembles English.",
    "question": "Do complete zero-offset additive or subtractive streams of two LP2 pages yield English-like GP labels?",
    "targets": targets,
    "pairing": "Every unordered pair of distinct nonempty LP2-00–55 pages (1,485 pairs). Align at rune ordinal zero; stop at the shorter page. No repeat, offset, reverse, header exclusion or key reset.",
    "operations": ["A+B", "A-B", "B-A"],
    "arithmetic": "Compute each output GP rune index modulo 29. A+B is symmetric; subtraction directions are distinct for an English scorer. This gives 4,455 candidate streams before eligibility.",
    "score": "Translate output GP indices to canonical Latin rune labels, then average pinned base-10 English quadgram scores including 0.01-count unseen floor. Eligibility is at least 100 within-stream Latin quadgrams (four-letter groups). Retain the global highest eligible score with fixed pair-order tie breaking; output full text and every observed score.",
    "control": "256 shared conditional-band within-page shuffles, Python Random(33017127+t) per trial. Band limits are all observed page rune lengths not exceeding each page's own length, exactly as lp2-page-pair-alignment; this preserves each compared prefix's rune histogram. Shuffle each page once per trial and reuse across the entire 4,455-case grid. Compare global best observed with the global best of the same eligible grid in each trial; add-one estimate (1+exceedances)/257.",
    "positive_control": "Use the fixed known Warning GP reading as target output. Generate a deterministic independent 184-rune page key from Random(33017126), construct a synthetic second page that yields the reading for each of A+B, A-B and B-A, and verify exact index recovery and English score >−5.5. Also check arithmetic identities on small exhaustive F29 pairs.",
    "decision": "An ordinary global English score under matched whole-grid shuffles does not support these zero-offset direct additive readings. A high score needs a continuous independently inspectable passage, not just a model score.",
    "exclusions": "Offsets, repeated page keys, reverse page order, differing page extents, other operations, altered page order/transcription, further cipher layers, languages other than English and historical negative claims.",
    "model": "experiments/records/english-scorer-controls/english_quadgrams.txt",
    "inputs": [pinned(path) for path in paths]
}
(HERE / "plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
