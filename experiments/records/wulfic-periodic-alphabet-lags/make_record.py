"""Write a draft Stage AE replay record with all local dependencies hashed."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = f"experiments/records/{HERE.name}/"


def hashed(name: str) -> dict[str, str]:
    return {"path": name, "sha256": hashlib.sha256((ROOT / name).read_bytes()).hexdigest()}


if __name__ == "__main__":
    pages = [f"lp2-{n:02d}" for n in range(56)]
    artifacts = [BASE + "source-stage_ae_lags.tsv", BASE + "source-stage_ae_controls.tsv"]
    inputs = [BASE + name for name in ("plan.json", "check.py", "plot.py", "replay_source.py",
                                       "make_plan.py", "make_record.py")]
    inputs += artifacts + ["data/index.json"] + [f"data/pages/{page}.json" for page in pages]
    record = {
        "id": HERE.name, "status": "draft",
        "title": "Repeating-alphabet periods across LP2",
        "question": "At which periods does LP2 preserve the rune agreement expected when the same bijective alphabet repeats?",
        "reader_question": "Could a repeating alphabet explain the rune patterns?",
        "summary": "An exact source replay checks all 12,935 periods. Under its controlled equality model, 10,030 are excluded, including 1033, 1729 and 3301; 2,905 remain open and none is positively detected.",
        "finding": "Stage AE's valid source run excludes 10,030 of 12,935 periods using its 5% plaintext-agreement model and binomial lower-tail rule. All 100 planted periodic controls passed and none was excluded; no LP2 lag passed the positive rule.",
        "limitations": "The result assumes a fixed bijective alphabet at each periodic residue, the source's English/LP1 controls, anti-doublet simulation and transcription. Lag-pair dependence and selection over 12,935 periods limit probability interpretation; other stateful or layered ciphers are not tested.",
        "next_steps": "For any remaining candidate period, specify a complete alphabet/key rule and test held-out output; for other periodic models, establish a fresh invariant and positive-control power before using absence of equality as evidence.",
        "outcome": "inconclusive",
        "tags": ["LP2", "source replay", "periodic key", "alphabet", "lag equality", "search bounds"],
        "scope": {
            "pages": pages, "artifacts": artifacts,
            "representation": "The joined 12,956-rune LP2 sections 7–15 stream in canonical GP29 order, with punctuation and page/line breaks omitted for rune-lag counting.",
            "procedure": "Replay pinned Wulfic Stage AE source; independently reconstruct every rune-lag agreement count from site page text, three named binomial lower tails and a planted periodic bijection.",
            "parameters": "All 12,935 lags 11–12,945; p_H=0.050 lower-tail threshold exp(-10), positive threshold 0.01/12,935 against empirical p0; 20 anti-doublet flat nulls and 100 planted controls at five named periods from Emerson and LP1; source seed3301.",
            "exclusions": "Lags below11 or above12945, per-page resets, non-bijective or changing alphabets, keyed/drifting state, additional encryption layers, alternate transcriptions and languages with a different equality baseline."
        },
        "review": {
            "kind": "exact public-source replay with independent all-lag statistic check",
            "retested_on": "2026-10-23",
            "reviewer": "Two source TSVs reproduced byte-for-byte; all 12,935 LP2 counts independently reconstructed; named exact binomial tails and planted periodic bijection checked",
            "human_review": "pending"
        },
        "reproduction": {
            "command": "python " + BASE + "run.py --check && python " + BASE + "check.py && python " + BASE + "plot.py --check",
            "environment": "Python 3 standard library for bundled verification. Optional full source replay requires the pinned Wulfic checkout with NumPy.",
            "script": BASE + "run.py", "script_sha256": hashed(BASE + "run.py")["sha256"],
            "inputs": [hashed(name) for name in inputs],
            "outputs": [hashed(BASE + name) for name in ("results.json", "comparison.svg")]
        },
        "visuals": [{"path": BASE + "comparison.svg", "caption": "Named-period LP2 rune agreement against the lowest planted control, with the all-lag result below."}],
        "sources": [
            {"label": "Wulfic Stage AE at pinned revision", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_ae.py"},
            {"label": "Pinned source findings", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/tree/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/reference/findings"}
        ],
        "related": ["periodic-affine-crib-capacity", "lp2-31-periodic-ioc"]
    }
    (HERE / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
