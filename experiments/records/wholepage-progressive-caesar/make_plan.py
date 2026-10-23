"""Freeze the exact progressive-shift search before manuscript scoring."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
readings = ("warning", "welcome", "some-wisdom", "first-koan", "second-koan",
            "loss-of-divinity", "instruction", "lp2-56", "lp2-57")
paths = (["data/index.json", "experiments/records/english-scorer-controls/english_quadgrams.txt"]
         + [f"data/pages/lp2-{i:02d}.json" for i in range(56)]
         + [f"exports/readings/{name}.csv" for name in readings])
plan = {
    "schema": "liberpedia-wholepage-progressive-caesar-plan-v1",
    "question": "Does a constant-rate shift of the GP29 alphabet yield English-like complete text on any LP2-00–55 page?",
    "inputs": [{"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()} for path in paths],
    "pages": [f"lp2-{i:02d}" for i in range(56) if i != 50],
    "empty_page": "lp2-50",
    "readings": list(readings),
    "representation": "All archived runes on each page including headings; ignore non-runes; page-local rune ordinal i begins at zero and advances only on runes.",
    "schedules": "P_i=(C_i+k*i+b) mod 29, k=1..28 and b=0..28, 812 distinct nonconstant schedules per complete page. Both step directions and all starting phases are represented by k and b. k=0 static shifts excluded as already in the affine census.",
    "score": "Mean base-10 log likelihood of canonical GP Latin quadgrams, unseen count floor 0.01; fixed English threshold -5.5.",
    "score_threshold": -5.5,
    "positive_control_schedule": {"k": 7, "b": 13},
    "control_seed": 531564,
    "control_replicates": 200,
    "control_gate": "Use all runes of nine archived readings. At least eight score above -5.5 and above 99% of 200 own rune-order shuffles; at least eight planted schedules recover the true plaintext at rank one among all 812 schedules.",
    "null_seed": 531565,
    "null_replicates": 199,
    "global_null": "For each replicate, shuffle rune order independently within each of 55 pages, preserving page lengths/counts; evaluate all 44,660 page/schedule outputs and retain one global maximum. This is a positional null, not a cipher model.",
    "exclusions": "No static shifts (already covered), nonlinear clocks, word/line resets, mixed or permuted alphabets, independent Caesar layers, transposition, non-English text, or general Alberti disk mechanisms."
}
(HERE / "plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
