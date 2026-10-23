"""Freeze the archived key, target, model and control inputs."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
NAMES = ["warning", "welcome", "some-wisdom", "first-koan", "loss-of-divinity", "second-koan", "instruction", "lp2-57"]
SECTIONS = [{"id": name, "path": f"exports/readings/{name}.csv",
             "runes": sum(1 for _ in (ROOT / f"exports/readings/{name}.csv").open(encoding="utf-8")) - 1} for name in NAMES]
TARGETS = [f"lp2-{i:02d}" for i in range(56) if i != 50]
PATHS = (["data/index.json", "exports/readings/manifest.json",
          "experiments/records/english-scorer-controls/english_quadgrams.txt"]
         + [row["path"] for row in SECTIONS]
         + [f"text/{page}.txt" for page in TARGETS])
PLAN = {
    "schema": "liberpedia-solved-reading-running-key-plan-v1",
    "question": "Can the archived solved GP readings, used as one contiguous nonrepeating additive key, produce a whole LP2 page with stronger English quadgram evidence than the same complete search on shuffled source order?",
    "source_order": "Eight decoded GP index traces, sorted by first manuscript page LP1-01, 03, 05, 06, 10, 14, 16, then LP2-57. Concatenate sections without inserted rune or key reset. Exclude LP2-56 hash target.",
    "sections": SECTIONS,
    "targets": TARGETS,
    "cipher_rule": "For each target full GP29 rune stream, P[i]=(C[i]+sign*K[offset+i]) mod29, sign in {-1,+1}. Search every source offset where the entire page fits; no wrapping, skipped symbols, or resets inside a page. Punctuation does not consume a symbol.",
    "model": "experiments/records/english-scorer-controls/english_quadgrams.txt",
    "score": "Average base-10 English quadgram log likelihood of the entire decoded page after concatenating canonical GP Latin labels; unseen quadgram pseudo-count 0.01. No model is trained on the eight key readings.",
    "plant": {"plaintext_path": "exports/readings/warning.csv", "held_out_key_section": "warning", "key_section": "first-koan", "offset_in_section": 31,
              "rule": "For this planted control only, hold out the complete 184-rune Warning section from the source key, encrypt that reading under a First Koan key interval, then require exact decryption and top full-offset/sign recovery. The LP2 search still uses all eight sections. Holding out Warning avoids an algebraic source/plaintext swap that caused the first control design to rank a different valid English passage first; no LP2 scores were computed under that design."},
    "shuffle_seeds": list(range(33017100, 33017116)),
    "null": "For each seed, shuffle the entire 2,892-rune key once, preserving exact symbol counts, then repeat the complete page/offset/sign grid and save its single global maximum. Sixteen maxima have coarse p-value resolution 1/17; this is a descriptive comparison, not a general cipher exclusion.",
    "inputs": [{"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()} for path in PATHS]
}

if __name__ == "__main__":
    dest = HERE / "plan.json"
    if dest.exists():
        raise SystemExit("Plan already exists; refusing to rewrite frozen settings")
    dest.write_text(json.dumps(PLAN, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Frozen {len(SECTIONS)} source sections, {len(TARGETS)} target pages, {len(PLAN['shuffle_seeds'])} shared shuffles")
