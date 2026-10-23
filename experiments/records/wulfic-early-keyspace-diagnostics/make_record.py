"""Write metadata with hashes of the preserved source-replay bundle."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ID = HERE.name
BASE = f"experiments/records/{ID}/"


def hashed(name: str) -> dict[str, str]:
    path = ROOT / name
    return {"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main() -> None:
    rec = {
        "id": ID,
        "status": "draft",
        "title": "Four early keyspace checks on LP2",
        "question": "Do Wulfic's specified running-key, small-key, ciphertext-autokey and selected-alphabet diagnostics find their expected LP2 signal?",
        "reader_question": "Do LP2 rune patterns fit these running-key or autokey models?",
        "summary": "Pinned J/K/L source controls pass; two pooled unigram models fail their source line and two within-section lag searches find no corrected detection.",
        "finding": "All thirteen pinned test assertions pass. The strongest C10 and C13 pooled frequency LLRs are −14.38 and −14.27, below the source's −10 line. C11's minimum p is 0.000559 versus 0.00000501 after 1,998 lag/sign checks; C12's minimum approximate p is 0.003916 versus 0.00001 after 1,000 lags. The 12,956 source GP29 runes match Liberpedia's LP2 page text; an independent checker recalculates all 3,029 source manuscript rows.",
        "limitations": "C10/C13 depend on the source solved-LP1 plaintext distribution, independent key/plaintext values, fixed mappings and mixture weights; pooled unigram mismatch is not a search over every real English running key. C11/C12 are specific within-section diagnostics, not full decryptions or exclusions of arbitrary ciphertext feedback/substitution. The C12 tail uses Wilson-Hilferty approximation. Wide 60/100/256-value key alphabets lack power in this frequency test and are not rejected.",
        "next_steps": "A narrower feedback or running-key proposal needs an exact key schedule, section reset rule, corpus transformation and a planted control at its proposed length.",
        "outcome": "not-supported",
        "tags": ["LP2", "source replay", "running key", "ciphertext autokey", "alphabet substitution", "frequency analysis"],
        "scope": {
            "pages": [f"lp2-{i:02d}" for i in range(56)],
            "artifacts": [BASE + "plan.json", BASE + "inputs.json"],
            "representation": "Source GP29 canonical rune values in nine segments 7–15 over LP2-00–55; 12,956 positions, checked against all site page raw texts.",
            "procedure": "Run unchanged pinned test_keyspace.py (13 assertions with synthetic controls); retain its exact C10–C13 manuscript score grids and model inputs; independently recalculate every score and compare source/site runes.",
            "parameters": "C10: 3 maps×3 modes×3 mixtures, best of 29 offsets. C11: 999 lags×2 signs. C12: 1,000 lags. C13: four source key-value distributions, best of 3 modes×29 offsets. Source −10-nat and Bonferroni .01 thresholds.",
            "exclusions": "Other plaintext corpora or distributions, key/plaintext dependence, alternate GP mappings, word/page resets, lag >1,000, nonlinear feedback, additional layers and direct decryption quality."
        },
        "review": {"kind": "exact pinned public-source J/K/L test replay with independent all-row numeric checker",
                   "retested_on": "2026-10-23", "reviewer": "13 source assertions passed; 3,029 manuscript rows and 12,956 GP29 rune positions independently recalculated/compared", "human_review": "pending"},
        "reproduction": {"command": f"python {BASE}check.py && python {BASE}plot.py --check",
                         "environment": "Python 3 standard library; optional source replay needs the pinned Wulfic Git checkout.",
                         "script": BASE + "check.py", "script_sha256": hashed(BASE + "check.py")["sha256"],
                         "inputs": [hashed(BASE + n) for n in ("plan.json", "inputs.json", "replay_source.py", "plot.py")]
                         + [hashed(f"data/pages/lp2-{i:02d}.json") for i in range(56)],
                         "outputs": [hashed(BASE + n) for n in ("results.json", "comparison.svg")]},
        "visuals": [{"path": BASE + "comparison.svg", "caption": "The nearest result in each source diagnostic, shown beside its own decision line."}],
        "sources": [{"label": "Wulfic pinned source tests", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tests/test_keyspace.py"},
                    {"label": "Wulfic model arithmetic", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/lpcore/stats.py"}],
        "related": ["wulfic-position-alphabet-flatness-bound", "solved-reading-running-key"]
    }
    (HERE / "record.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
