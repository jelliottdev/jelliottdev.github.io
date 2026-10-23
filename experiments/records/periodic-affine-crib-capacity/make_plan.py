"""Pin the periodic-affine crib-count census before any LP2 fit is measured."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
paths = (["data/index.json", "experiments/records/lp2-known-vigenere-keys/plan.json",
          "exports/readings/warning.csv"]
         + [f"data/pages/lp2-{i:02d}.json" for i in range(56)])
plan = {
    "schema": "liberpedia-periodic-affine-crib-capacity-plan-v1",
    "question": "How often can a fixed twelve-rune proposed opening fit a period-p sequence of invertible GP29 affine maps, and how much of the following text does that fit actually constrain?",
    "inputs": [{"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()} for path in paths],
    "pages": [f"lp2-{i:02d}" for i in range(56) if i != 50],
    "empty_page": "lp2-50",
    "crib_source": "First 12 rune indices of nine archived solved readings as frozen in lp2-known-vigenere-keys/plan.json; no other words or alignment positions.",
    "selection": "First 24 runes of each LP2 page including headings; first 12 as ciphertext paired with each fixed crib, following 12 only for forced-position count. Rune position i begins at page start; ignore non-runes.",
    "model": "P_i=(a_(i mod p)*C_i+b_(i mod p)) mod 29, each a in 1..28 and b in 0..28; p=1..8. No clock reset within the 24-rune window.",
    "counting": "For each residue independently enumerate all 812 invertible (a,b) pairs that satisfy its crib positions. With at least one observation per residue, count is 0,1,or28; multiply the p slot counts for total compatible keys. If total>0, count following positions whose plaintext is identical under all compatible maps for their residue. Do not select or score a continuation.",
    "planted_control": {"reading": "warning", "length": 24, "period": 3,
                        "maps": [{"a": 3, "b": 7}, {"a": 5, "b": 11}, {"a": 9, "b": 2}],
                        "expectation": "The first 12 known plaintext runes identify one complete 3-slot key and force all next 12 true output indices."},
    "toy_control": "Over F3, for three fixed length-six ciphertext patterns and every 3^6 proposed plaintext, compare residue-factorized counts for periods 1..3 with exhaustive enumeration of all 6^p keys; this checks impossible, unique and ambiguous fits.",
    "interpretation": "A compatible key is an algebraic fit to a supplied 12-rune opening, not evidence of a decryption. A forced next symbol is a prediction conditional on that crib and exact period/model, not a validation against unknown plaintext.",
    "exclusions": "No other cribs, later alignments, p>8, mixed alphabets, noninvertible maps, period changes, word/line reset, feedback, English score, or historical Alberti disk branches."
}
(HERE / "plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
