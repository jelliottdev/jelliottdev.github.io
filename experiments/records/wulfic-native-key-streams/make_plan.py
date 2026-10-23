"""Regenerate exact input hashes for the source-grid and supplemental-control record."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


if __name__ == "__main__":
    paths = [
        "experiments/records/wulfic-native-key-streams/source-stage_i_candidates.tsv",
        "experiments/records/wulfic-native-key-streams/source-stage_m_candidates.tsv",
        "experiments/records/wulfic-native-key-streams/supplemental-controls.tsv",
        "experiments/records/wulfic-stage-ab-reset-alphabets/layout.json",
        "experiments/records/wulfic-stage-ab-reset-alphabets/check.py",
        "exports/alphanumeric-grids.csv", "data/index.json",
        *(f"data/pages/lp2-{i:02d}.json" for i in range(56)),
    ]
    plan = {
        "schema": "liberpedia-wulfic-native-key-streams-plan-v1",
        "source": {
            "repository": "https://github.com/Wulfic/Cicada3301-Liber_Primus",
            "commit": "bf89d3d13aad2b8f2c95ab195cf1b092f250775c",
            "stage_i": "tools/run_stage_i.py",
            "stage_i_sha256": "7582b46f446338780ed4e3c4429bf3b70a2e1feed061d11ef4cc7f5a2fc962d6",
            "stage_m": "tools/run_stage_m.py",
            "stage_m_sha256": "eefb61156135a799039452e67a4973cd28b22952fcd2c643630fedbd70a5a7bb",
            "detect_sha256": "fc0f0fb715e888f9ffe0ee434f786f273a0ee939ab050d54ff4e369a8f301eeb",
            "keys_sha256": "551f5c0c4746c934b2317b22562fd95db969600dda2bfbe2a3ab7c359255cafc",
            "source_master_sha256": "df7eaaa0c92243946803a7a90a7bfdcb36c0eba73f964f3a093c238ab01a5746",
            "source_translation_sha256": "adce48cfea746fd5add5071c85a34a998a546ca94c009bcd796cd3e699cc1c47",
        },
        "source_grids": {
            "I": "Primes, solved-LP1 word prime sums, and solved-LP1 rune prime values; each at nine sections and the continuous stream, three directions, 29 shifts: 2,610 rows.",
            "M": "Grid bytes (256), regrouped 5-bit units (409), base-60 digits (512), reduced mod 29; nine sections, continuous stream, after-grid and ending-at-grid alignments, three directions, 29 shifts: 3,132 rows.",
            "model": "Pinned detector: fixed start 0, drift steps stay/advance/skip with rho .02, epsilon .1, solved-LP1 unigram emission, neutral emission after key exhaustion.",
            "pass": "Log likelihood ratio >= +30 nats.",
        },
        "source_key_fingerprints": {
            "K-A primes": "21484ebeec3a48f084a07c485a54c91d3bf3eb532ef6fa42efeec374b5f6e42f",
            "K-C word sums": "72ee8dc04c0245b8c3544e79216cfc5dbfe28d660344c3dc917d304edb019bcd",
            "K-D plaintext values": "db5ce0b1993c9788034da908a3573af72664ceb02acc5338f47da0623a584931",
            "G-B bytes": "b620df97ccff1e1bb9458f9c7c4180b64a52c0aab85b98a9b1ca876b1558ba2b",
            "G-5 5-bit groups": "8bd480801a4cd705bb6f15a2cbf242795e1e348a60a338b671c110accac169bc",
            "G-D base-60 digits": "4ac95ea32d8c107e9ba788a84aa30421aa2596a40f7577c9f58a3958313b7145",
        },
        "supplemental_diagnostic": {
            "status": "Designed after seeing the source LP2 scores; a power check, not a pre-LP2 preregistered source control.",
            "seed_values": list(range(3301, 3321)),
            "lengths": {"K-A primes": 729, "K-C word sums": 650, "K-D plaintext values": 729,
                        "G-B bytes": 230, "G-5 5-bit groups": 368, "G-D base-60 digits": 460},
            "rule": "At fixed start 0, encrypt a solved-LP1 rune window using each pinned key and anti-doublet next-key redraw, then score with the exact source detector; also score the same ciphertext with a seeded wrong key. Report pass counts of 20 each at +30.",
        },
        "exclusions": "Not a search over key offsets, alternate grid glyphs, cyclic repetition, other mappings or plaintext priors. The source's separate nine-rune square-title vocabulary test is outside this grouped stream experiment.",
        "inputs": [{"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}
                   for path in paths],
    }
    (HERE / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
                                     encoding="utf-8", newline="\n")
