"""Freeze the input inventory and search rules before scoring manuscript pages."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
paths = (["data/index.json", "experiments/records/lp2-known-vigenere-keys/plan.json",
          "experiments/records/english-scorer-controls/english_quadgrams.txt"]
         + [f"data/pages/lp2-{i:02d}.json" for i in range(56)]
         + [f"exports/readings/{name}.csv" for name in
            ("warning", "welcome", "some-wisdom", "first-koan", "second-koan",
             "loss-of-divinity", "instruction", "lp2-56", "lp2-57")])
plan = {
    "schema": "liberpedia-wholepage-known-keys-plan-v1",
    "question": "Do either of two documented LP1 repeating keys make any complete unsolved LP2 rune page resemble the archived English controls?",
    "inputs": [{"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()} for path in paths],
    "pages": [f"lp2-{i:02d}" for i in range(56) if i != 50],
    "empty_page": "lp2-50",
    "selection": "All runes on each page, including headings, in archived line order; non-runes do not advance the key; reset each page.",
    "keys": ["welcome", "second-koan"],
    "settings": "All zero-based phases of each key, both arithmetic signs; 55 pages times 42 settings = 2310 full-page outputs.",
    "score": "Mean base-10 log likelihood of canonical GP Latin transliteration quadgrams, floor count 0.01; higher is more English-like.",
    "score_threshold": -5.5,
    "controls": "First 66 runes from each of nine archived solved-reading traces; each vs 200 seeded rune-order shuffles; nine planted encipherments each searched under the same 42 settings. Require at least eight genuine controls above threshold and above 99 percent of own shuffles, and at least eight planted keys ranked first.",
    "control_length": 66,
    "control_replicates": 200,
    "control_seed": 531560,
    "global_null": "199 seeded replicates: shuffle rune order independently within every page, preserving each page's rune counts and length; rerun all 2310 settings; retain the single highest score across the full search.",
    "null_replicates": 199,
    "null_seed": 531561,
    "limitations": "No other keys, resets at punctuation, wordwise state, alternative rune mappings, transposition, other language, or key layer. A positional shuffle is not an encryption model."
}
(HERE / "plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
