"""Freeze the full-stream readability extension of the existing 16 routes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
route_plan = json.loads((ROOT / "experiments/records/lp2-row-column-routes/plan.json").read_text(encoding="utf-8"))
targets = [page for page in route_plan["pages"] if page != "lp2-50"]


def pin(path: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


inputs = ["data/index.json", "data/evidence/known-readings.json",
          "experiments/records/english-scorer-controls/english_quadgrams.txt",
          "experiments/records/lp2-row-column-routes/plan.json",
          "experiments/records/lp2-row-column-routes/results.json",
          "research/source-archive/lp2-collected-solution-ideas-2026-10-23.txt"]
inputs += [f"text/{page}.txt" for page in targets]
plan = {
    "schema": "liberpedia-row-column-english-plan-v1",
    "frozen_before_scoring": "2026-10-23",
    "source_idea": "User-supplied solution-idea catalog item 9.2, its columnar component. The 16 exact ragged ordinal routes are taken unchanged from the published lp2-row-column-routes plan/results; this is a new full-stream score, not a historical replay.",
    "prior_overlap": "lp2-row-column-routes checked nine exact 12-rune openings across the same 880 route outputs; it did not test full-stream English readability. rail-fence-visible-words is a different rail-permutation and dictionary test.",
    "question": "Does any complete row/ordinal-column route make a whole LP2 page English-like under canonical GP transliteration?",
    "targets": targets,
    "route_rules": "For each rune-bearing page use the archived line-by-line rune rows, left-aligned by rune ordinal. The fixed Cartesian grid is axis row/column × outer direction forward/backward × initial inner direction forward/backward × alternate inner direction no/yes. Alternation uses visited-group ordinal. Missing cells are skipped. Every route is a bijection over all page rune positions.",
    "reuse": "Use the published route outputs and source_ordinals only after verifying their pinned result SHA-256; the independent checker reconstructs all 16 permutations from structured page JSON and coordinate ordering keys.",
    "score": "Translate all output GP indices to canonical Latin labels and average pinned base-10 English quadgram scores with 0.01-count unseen floor. Eligibility requires at least 100 within-page four-letter groups. Report all 880 scores and the full best output. Since every route preserves a page's rune multiset, eligibility does not vary among that page's routes or its shuffles.",
    "null": "Exactly 256 shared complete searches: Random(33017128+t) shuffles each page's rune indices once while keeping its observed line lengths and ordinal column shape. Reuse the same 55 shuffled pages across all 16 routes in that trial. Retain the best eligible of all 880 routes. Compare to best observed with add-one (1+#max>=observed)/257.",
    "positive_control": "Take the first N GP rune indices of the fixed 515-rune Welcome decoded reading, where N equals LP2-31's 269 positions. For each of the 16 LP2-31 routes, place the intended output indices into source positions by the inverse route; verify exact roundtrip and English score >−5.5. Hand-check ragged ABC/DE/F row and column routes as in the earlier record.",
    "decision": "A high score must produce a continuous readable passage; a best score ordinary under a matched full-route null does not support these pure permutations. Physical image columns, diagonals, rectangle reflow and substitutions are outside scope.",
    "exclusions": "Physical image-coordinate alignment, diagonals, spirals, a rectangular grid or padding, arbitrary row/column permutations, combined substitution or transposition across pages, other languages, short excluded pages and historical-negative claims.",
    "model": "experiments/records/english-scorer-controls/english_quadgrams.txt",
    "inputs": [pin(path) for path in inputs]
}
(HERE / "plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
