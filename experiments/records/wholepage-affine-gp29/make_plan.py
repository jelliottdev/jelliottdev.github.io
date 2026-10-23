"""Freeze the exact whole-page affine search and source hashes before scoring."""
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
    "schema": "liberpedia-wholepage-affine-gp29-plan-v1",
    "question": "Does any one fixed invertible affine map of the 29 GP rune indices make a complete LP2-00–55 page resemble archived English readings?",
    "inputs": [{"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()} for path in paths],
    "pages": [f"lp2-{i:02d}" for i in range(56) if i != 50],
    "empty_page": "lp2-50",
    "readings": list(readings),
    "representation": "All archived runes on each page including headings; ignore non-runes; keep page order; independent page results.",
    "maps": "P=(a*C+b) mod 29, every a=1..28 and b=0..28, 812 maps; one static map per complete page. Atbash and every Caesar shift are included once.",
    "score": "Mean base-10 log likelihood of canonical GP Latin quadgrams, unseen count floor 0.01; fixed English threshold -5.5.",
    "score_threshold": -5.5,
    "positive_control_map": {"a": 7, "b": 13},
    "control_seed": 531562,
    "control_replicates": 200,
    "control_gate": "Use all runes of each of nine archived readings. At least eight score above -5.5 and above 99% of 200 own rune-order shuffles; at least eight recovered planted plaintexts rank first among all 812 affine maps.",
    "null_seed": 531563,
    "null_replicates": 199,
    "global_null": "For each replicate, shuffle rune order independently within each of 55 pages, preserving page lengths and counts; evaluate all 44,660 page/map outputs and retain the one global maximum. This is a positional null, not a cipher model.",
    "exclusions": "No period-dependent affine rule, interrupted or wordwise map, general substitution permutation, different alphabet, transposition, other language, or hidden intermediate layer."
}
(HERE / "plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
