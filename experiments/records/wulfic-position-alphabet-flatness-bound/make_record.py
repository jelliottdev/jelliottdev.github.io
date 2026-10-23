"""Refresh Stage T draft metadata and declared file hashes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = f"experiments/records/{HERE.name}/"


def digest(relative: str) -> dict[str, str]:
    return {"path": relative, "sha256": hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()}


def main() -> None:
    inputs = [BASE + filename for filename in
              ("plan.json", "check.py", "plot.py", "replay_source.py", "make_record.py",
               "source-stage_t_results.tsv")]
    outputs = [BASE + filename for filename in ("results.json", "comparison.svg")]
    record = {
        "id": HERE.name, "status": "draft",
        "title": "Random-alphabet flatness bound on LP2",
        "question": "How many independent substitution alphabets per key class are needed before LP2's rune frequencies cease to contradict that model?",
        "reader_question": "Can LP2's flat rune counts rule out small sets of random alphabets?",
        "summary": "Exact Stage T replay reproduces a conditional lower-tail bound: at the source threshold, up to 168 effective key classes are excluded for one alphabet set, or up to 174 when each selected section gets a fresh set.",
        "finding": "All declared source control gates pass. The 12,956-rune pooled statistic is 26.36; the eight-section statistic is 194.14 across 12,947 runes. Under the independent-random-permutation model, effective class counts through 168 pooled or 174 sectioned meet the source's 0.0001 exclusion rule. No plaintext or key is identified.",
        "limitations": "These are source-calibrated model bounds, not cryptographic impossibility results. The independent random-permutation assumption, solved-LP1 frequency calibration, and source section choices matter. Latin-square/additive ciphers, correlated alphabets and layers are outside scope. The reported 153/133 sensitivity is post-run, not the original decision rule.",
        "next_steps": "A proposed short-key alphabet system should specify whether its alphabets are independent random permutations. Different structured tabulae require direct decryption tests or appropriate controls.",
        "outcome": "inconclusive",
        "tags": ["LP2", "source replay", "alphabet substitution", "frequency analysis", "search bounds"],
        "scope": {
            "pages": [f"lp2-{i:02d}" for i in range(56)],
            "artifacts": [BASE + "source-stage_t_results.tsv"],
            "representation": "Canonical 29-rune indices from LP2-00–55, pooled or grouped by the source's marked sections 7–9 and 11–15. The sectioned rule omits the nine-rune section 10.",
            "procedure": "Run pinned Stage T's full synthetic gates and Monte Carlo reference; independently reconstruct manuscript rune counts and chi-square values from Liberpedia page records, check the pooled analytic boundary, and verify source decisions.",
            "parameters": "200 synthetic controls each at V=29,256,1024; source alpha 0.0001; eight selected sections; 2,000,000 seeded chi-square reference draws for the sectioned model; 20 named key-class schemes.",
            "exclusions": "Vigenere/Latin-square or other structured alphabets, alternate plaintext distributions, different segmentation, transposition, additional layers and any key recovery."
        },
        "review": {
            "kind": "exact public-source Stage T replay with independent site-corpus statistics",
            "retested_on": "2026-10-23",
            "reviewer": "All 45 pinned source rows reproduced byte-for-byte; separate site page parser reproduces rune counts and chi-square values and independently checks the pooled boundary",
            "human_review": "pending"
        },
        "reproduction": {
            "command": f"python {BASE}run.py --check && python {BASE}plot.py --check",
            "environment": "Bundled checks need Python 3 standard library. Optional full pinned-source Monte Carlo replay needs NumPy and an external source checkout.",
            "script": BASE + "run.py", "script_sha256": digest(BASE + "run.py")["sha256"],
            "inputs": [digest(path) for path in inputs],
            "outputs": [digest(path) for path in outputs]
        },
        "visuals": [{"path": BASE + "comparison.svg",
                     "caption": "Largest excluded effective class count for each of the source's two independent-random-alphabet models; no decryption is implied."}],
        "sources": [
            {"label": "Pinned Wulfic Stage T source", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_t.py"},
            {"label": "Pinned source flatness derivation", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/lpcore/flatness.py"},
            {"label": "Pinned source results", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/reference/findings/stage_t_results.tsv"}
        ],
        "related": ["wulfic-position-alphabet-long-keys", "wulfic-native-key-streams", "doublet-placement"]
    }
    (HERE / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
