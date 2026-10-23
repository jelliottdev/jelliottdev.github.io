"""Freeze the bounded GP-prime plaintext-feedback baseline before LP2 scoring."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def main() -> None:
    targets = [f"lp2-{i:02d}" for i in range(56) if i != 50]
    paths = ["data/index.json", "exports/readings/warning.csv",
             "experiments/records/english-scorer-controls/english_quadgrams.txt"]
    paths += [f"text/{page}.txt" for page in targets]
    inputs = [{"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}
              for path in paths]
    plan = {
        "schema": "liberpedia-gp-prime-plaintext-feedback-plan-v1",
        "status": "bounded-new-baseline-not-historical-replay",
        "source": "User-supplied, incompletely specified numerical/gematria autokey idea; these two exact equations are our test definitions, not attributed to the user or Cicada.",
        "overlap": {
            "source_W5": "Pinned Dukotah wordsum_selfkey.py W5 uses prime(previous C) with index-0 primer; excluded from this test.",
            "source_W1_W4": "Pinned source word-sum feedback variants use word boundaries; excluded.",
            "existing": ["cumulative-autokey-literal", "public-multihistory-feedback", "wulfic-autokey-seed-families", "feedback-opening-census", "crib-inferred-feedback-table", "solved-reading-running-key"],
            "difference": "Full-page plaintext GP-prime-valued feedback, either previous-rune or cumulative-sum, not fixed GP index feedback or 12-rune partial-table compatibility."
        },
        "targets": targets,
        "inputs": inputs,
        "alphabet": "GP29 order and prime column in data/index.json; g(x)=prime[x] mod 29.",
        "equations": {
            "previous_plaintext_prime": "P[0]=(C[0]-e*s) mod29; P[i]=(C[i]-e*g(P[i-1])) mod29 for i>=1.",
            "cumulative_plaintext_prime": "S[0]=s; P[i]=(C[i]-e*S[i]) mod29; S[i+1]=(S[i]+g(P[i])) mod29."
        },
        "arms": ["previous_plaintext_prime", "cumulative_plaintext_prime"],
        "seeds": list(range(29)),
        "signs": [-1, 1],
        "boundaries": "Start each complete page independently at first rune; ignore punctuation and line/word boundaries; no skips, per-word resets, cross-page state or repeated whole-text pass.",
        "score_model": "experiments/records/english-scorer-controls/english_quadgrams.txt",
        "score_rule": "Mean base-10 log likelihood over every overlapping A-Z quadgram after concatenating canonical Latin labels for each output GP rune; unseen count 0.01.",
        "selection": "Search all 2 arms x 29 seeds x 2 signs x 55 nonempty complete LP2-00..55 pages = 6,380 candidates. Report every observed score, each page winner, global winner, and complete-grid null maxima.",
        "positive_controls": "Read all 184 GP indices from the archived LP1 Warning known-reading trace. For both arms, each sign, and every seed 0..28, encrypt then decode exactly. For seeds 0,7,28 under both signs and arms, require that the entire 116-configuration search ranks a candidate with exact original Warning plaintext at its maximum score; check model order before interpreting LP2.",
        "null": "For each fixed seed 33017200..33017398 inclusive, independently shuffle rune order within each of all 55 LP2 pages once with Python random.Random(seed), then run the unchanged complete 116-config-per-page search and record its single global maximum. One shared shuffled corpus per trial preserves dependence across arms/seeds/signs/pages. Conditional on page lengths and rune counts only; not a cipher mechanism.",
        "interpretation": "A high English score is a lead, not a reading. No inference about a general gematria autokey or the undefined 'shedding' operation. The parable sums/product and 761 reduce to members of the already exhaustive seed 0..28 domain and are not separate hypotheses."
    }
    (HERE / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("frozen plan:", hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
