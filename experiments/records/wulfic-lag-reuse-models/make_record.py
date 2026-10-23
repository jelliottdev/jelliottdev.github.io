"""Refresh grouped AC/AD record metadata and declared file hashes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = f"experiments/records/{HERE.name}/"


def hashed(path):
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main():
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    ac, ad = result["ac"], result["ad"]
    assert (ac["lag_rows"], ac["control_rows"], ac["pmax"], ac["mmin"]) == (12935, 138, 12500, 3000)
    assert (ad["lag_rows"], ad["control_rows"], ad["pmax"], ad["mmin"]) == (12935, 184, 12900, 200)
    assert ac["best"] == {"F": 7.05, "S-forward": 19.86, "S-reverse": 18.23}
    assert ad["best"] == {"F": 5.3, "S-forward": 22.49, "S-reverse": 23.16}
    assert ad["best_F_lag"] == 12942 and ad["best_F_pairs"] == 14 and ad["best_F_absolute_bound"] < 30
    inputs = [BASE + name for name in (
        "plan.json", "replay_source.py", "prepare.py", "collect.py", "make_results.py", "plot.py",
        "make_record.py", "source-stream.bin", "source-model.json",
        "source-stage_ac_lags.tsv", "source-stage_ac_top.tsv", "source-stage_ac_controls.tsv",
        "source-stage_ad_lags.tsv", "source-stage_ad_top.tsv", "source-stage_ad_controls.tsv",
    )]
    record = {
        "id": HERE.name, "status": "draft",
        "title": "Repeated keys and ciphertext autokeys at every lag",
        "question": "Do fixed shifted or reflected key-reuse laws, or LP2 ciphertext used as its own key, produce a calibrated whole-lag or reused-stretch signal?",
        "reader_question": "Could a key or ciphertext segment repeat elsewhere in LP2?",
        "summary": "Amended-source replay of two complete forward/reverse lag searches finds no +30 detection under either declared model, with original controls and null gates passing.",
        "finding": "After correcting only an original one-row control-array allocation in memory, all six AC/AD source result tables reproduce byte-for-byte. AC's best whole-lag, forward-stretch and reverse-stretch scores are +7.05, +19.86 and +18.23; AD's are +5.30, +22.49 and +23.16. All are below +30. AD's +5.30 whole-lag maximum has only 14 pair opportunities and an absolute +17.41 ceiling, so cannot pass at any key. The 138 AC and 184 AD planted-control rows match; both four-null gates are valid. Source/site GP29 text agrees across 12,956 positions, with selected pair-law scores independently recomputed.",
        "limitations": "The source programs cannot run unchanged: both crash in one-row reuse controls. The in-memory shape correction is disclosed and all original tables must match before accepting a result. AC's whole-lag exclusions are calibrated only through gap 12,500 and its all-cell reused-stretch detection only from 3,000 runes; AD's corresponding bounds are 12,900 and 200. The AD maximum whole-lag score comes from an underpowered 14-pair tail. Other pair laws, word resets, changing keys, language models or later decoding layers remain untested.",
        "next_steps": "A related proposal should state the exact pair relation, gap or stretch geometry and expected full output before testing, with a planted control at the claimed length.",
        "outcome": "not-supported",
        "tags": ["LP2", "source replay", "key reuse", "ciphertext autokey", "lag", "reverse pairing"],
        "scope": {
            "pages": [f"lp2-{i:02d}" for i in range(56)],
            "artifacts": [BASE + "source-stage_ac_lags.tsv", BASE + "source-stage_ad_lags.tsv"],
            "representation": "The source's continuous 12,956 GP29 rune values for LP2-00–55, verified identical to the site page transcription.",
            "procedure": "Repair only AC's one-row control cumsum allocation in memory. Reproduce AC and AD full original planted-control grids, four anti-doublet null streams each, all forward lags 11 through N−11 and all eligible reverse anti-diagonals. AC tests three pair laws ×29 shifts; AD tests four ×29. Compare every generated lag, top and control TSV byte with the pinned source; independently recompute representative scores.",
            "parameters": "AC: 12,935 forward lags, 3 relations, 29 shifts, 138 control rows, Pmax 12,500/Mmin 3,000. AD: same 12,935 lag rows, 4 relations, 29 shifts, 184 control rows, Pmax 12,900/Mmin 200. Fixed +30 positive line and −10 calibrated exclusion line; four null streams per stage. Source-provided control draws and seeds retained.",
            "exclusions": "Different text layers, page/word resets, lag under 11, other pair laws or plaintext priors, adaptive shifts, keys with nonlinear evolution, and reused stretches shorter than each calibrated control bound."
        },
        "review": {
            "kind": "pinned public-source AC/AD replay with disclosed one-line runtime repair and independent pair-score checks",
            "retested_on": "2026-10-23",
            "reviewer": "All six pinned tables and 322 planted-control rows reproduced byte-for-byte after in-memory source shape fix; two four-null validity gates passed; site runes and sampled source F/S scores independently checked",
            "human_review": "pending"
        },
        "reproduction": {
            "command": f"python {BASE}check.py && python {BASE}plot.py --check",
            "environment": "Python 3 and NumPy. The full amended-source replay additionally needs the pinned external Wulfic checkout at the stated commit.",
            "script": BASE + "check.py", "script_sha256": hashed(BASE + "check.py")["sha256"],
            "inputs": [hashed(path) for path in inputs],
            "outputs": [hashed(BASE + name) for name in ("results.json", "comparison.svg")]
        },
        "visuals": [{"path": BASE + "comparison.svg", "caption": "Best whole-lag and stretch scores from both source models, each below the +30 pass line. Source control power is bounded by tested gap and stretch lengths."}],
        "sources": [
            {"label": "Pinned Wulfic Stage AC source", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_ac.py"},
            {"label": "Pinned Wulfic Stage AD source", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_ad.py"},
            {"label": "Pinned AC result table", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/reference/findings/stage_ac_lags.tsv"},
            {"label": "Pinned AD result table", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/reference/findings/stage_ad_lags.tsv"}
        ],
        "related": ["wulfic-periodic-alphabet-lags", "multiplicative-ciphertext-autokey", "short-window-lag13"]
    }
    (HERE / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
