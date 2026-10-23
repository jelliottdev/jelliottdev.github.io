"""Refresh Stage U draft metadata and local file hashes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = f"experiments/records/{HERE.name}/"


def hashed(path: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main() -> None:
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    inputs = [BASE + x for x in ("plan.json", "check.py", "plot.py", "replay_source.py",
                                  "make_record.py", "source-stage_u_results.tsv")]
    record = {
        "id": HERE.name, "status": "draft",
        "title": "Random Quagmire alphabet families on LP2",
        "question": "Do the specified random-alphabet Quagmire mixtures yield rune counts as even as LP2's under six key-value distributions?",
        "reader_question": "Do random Quagmire alphabets fit LP2's rune frequencies?",
        "summary": "Exact Stage U replay finds 20 powered exclusions and four untestable settings across six key-value distributions, tied/independent alphabet variants and pooled/sectioned analyses.",
        "finding": "All source model and calibration gates pass. Twenty of 24 settings meet its strict raw and anti-doublet-adjusted lower-tail exclusion rule with power on at least 18/20 flat-key controls. Four uniform A–Z settings are untestable because their positive-control power is insufficient. No plaintext or key is produced.",
        "limitations": "This is a frequency screen for the source's random-alphabet Quagmire model and six key distributions. A–Z settings remain open under the source rule. Deterministic keyword alphabets, other key distributions or boundary rules, exact key order and layered ciphers are outside scope.",
        "next_steps": "A surviving Quagmire proposal needs a fixed key-value distribution, alphabet construction and further prediction beyond a favorable frequency statistic, with same-family controls.",
        "outcome": "inconclusive",
        "tags": ["LP2", "source replay", "Quagmire", "alphabet substitution", "frequency analysis", "control power"],
        "scope": {
            "pages": [f"lp2-{i:02d}" for i in range(56)],
            "artifacts": [BASE + "source-stage_u_results.tsv"],
            "representation": "Canonical 29-rune LP2-00–55 stream; pooled across 12,956 runes or grouped into source sections 7–9 and 11–15 for a separate fresh-alphabet statistic.",
            "procedure": "Run pinned Stage U's G1 model calibration, G2 flat-key power and G3 same-family false-exclusion checks, then score all 24 LP2 settings. Independently rebuild both manuscript chi-square statistics and audit each source verdict.",
            "parameters": "Six declared key-value distributions x two tied/independent alphabet variants x pooled/sectioned statistics; 100,000 model draws per reference; 200 anti-doublet-factor ciphers per statistic; 20 power and 20 same-family controls per setting; raw and adjusted P<=0.0001, power>=18/20.",
            "exclusions": "Other key distributions, nonrandom or named alphabets, key-order recovery, alternative boundaries, layers and decryption quality."
        },
        "review": {
            "kind": "exact public-source Stage U replay with independent manuscript and verdict checks",
            "retested_on": "2026-10-23",
            "reviewer": "Pinned source table reproduced byte-for-byte; 80 rows, all G1/G2/G3 and LP2 decisions audited; site page text independently reproduces pooled and sectioned chi-square statistics",
            "human_review": "pending"
        },
        "reproduction": {
            "command": f"python {BASE}run.py --check && python {BASE}plot.py --check",
            "environment": "Bundled checks use Python 3 standard library. Optional full source replay requires NumPy and a pinned external checkout; its simulations may take several minutes.",
            "script": BASE + "run.py", "script_sha256": hashed(BASE + "run.py")["sha256"],
            "inputs": [hashed(x) for x in inputs],
            "outputs": [hashed(BASE + x) for x in ("results.json", "comparison.svg")]
        },
        "visuals": [{"path": BASE + "comparison.svg",
                     "caption": "Powered exclusions for six key-value distributions, each under four source alphabet/section combinations; the uniform A–Z combination lacks power."}],
        "sources": [
            {"label": "Pinned Wulfic Stage U source", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_u.py"},
            {"label": "Pinned published Stage U results", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/reference/findings/stage_u_results.tsv"},
            {"label": "Pinned Quagmire model", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/lpcore/quagmire.py"}
        ],
        "related": ["wulfic-position-alphabet-flatness-bound", "wulfic-position-alphabet-long-keys", "quagmirror-six-rune-replay"]
    }
    assert result["excluded"] == 20 and result["untestable"] == 4
    (HERE / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
