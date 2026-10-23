"""Refresh Stage V draft metadata and local file hashes."""
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
    assert result["source_rows"] == 10357
    assert result["source_gate_G1_passed"] and result["source_leads"] == 0
    assert result["keyword_alphabets"] == 68 and result["source_members_per_family"] == 314432
    inputs = [BASE + x for x in ("plan.json", "check.py", "plot.py", "replay_source.py",
                                  "make_record.py", "source-stage_v_results.tsv")]
    record = {
        "id": HERE.name, "status": "draft",
        "title": "Named keyword Quagmire alphabets on LP2",
        "question": "Do the source's named keyword alphabets and six key distributions produce LP2's whole-book rune frequencies?",
        "reader_question": "Do named keyword alphabets fit LP2's rune frequencies?",
        "summary": "Exact Stage V replay checks 68 named alphabets in all source-defined triples against six key-value distributions. No combination reaches the source's positive-lead threshold.",
        "finding": "The source calibration gate passes and there are no +10 leads. Four key distributions have all 314,432 combinations both control-powered and below the source's −10 exclusion cutoff. Hexadecimal digits leave 135 powered non-exclusions; uniform A–Z leaves 10,197, while 272,640 A–Z combinations lack power. No plaintext or key is recovered.",
        "limitations": "This is a unigram frequency screen of fixed named alphabets and independent key-value distributions, not a decryption. It does not test arbitrary keywords, actual key order, alternative boundaries, non-independent keys or layered ciphers. Raw source exclusions must not be confused with control-powered exclusions.",
        "next_steps": "A surviving proposal needs a specific keyword, key sequence and a prediction of rune order or plaintext beyond the observed frequency profile.",
        "outcome": "inconclusive",
        "tags": ["LP2", "source replay", "Quagmire", "keyword alphabets", "frequency analysis", "control power"],
        "scope": {
            "pages": [f"lp2-{i:02d}" for i in range(56)],
            "artifacts": [BASE + "source-stage_v_results.tsv"],
            "representation": "Canonical GP29 LP2-00–55 stream represented by its pooled 12,956-rune frequency vector.",
            "procedure": "Rerun pinned Stage V's G1 same-family model controls and G2 flat-key power screen, then audit all source family summaries and listed survivors. Independently reconstruct the site manuscript rune vector.",
            "parameters": "34 source-specified keywords yield 68 distinct alphabets including identity and inverse forms. All 68^3 alphabet triples for each of six key-value distributions, maximizing over three sign modes and 29 offsets; −10 exclusion, +10 lead, and at least 18/20 G2 flat-key exclusions for power.",
            "exclusions": "Other keywords or alphabet constructions, dependent or ordered keys, page-specific resets, alternate statistics and sequence-level decryption."
        },
        "review": {
            "kind": "exact public-source Stage V replay with independent manuscript and verdict audit",
            "retested_on": "2026-10-23",
            "reviewer": "Pinned source result reproduced byte-for-byte over 10,357 rows; all G1/G2 family and survivor verdicts audited; site pages independently reproduce the 29-rune input counts",
            "human_review": "pending"
        },
        "reproduction": {
            "command": f"python {BASE}run.py --check && python {BASE}plot.py --check",
            "environment": "Bundled checks use Python 3 standard library. Optional full source replay requires NumPy and a pinned external checkout.",
            "script": BASE + "run.py", "script_sha256": hashed(BASE + "run.py")["sha256"],
            "inputs": [hashed(x) for x in inputs],
            "outputs": [hashed(BASE + x) for x in ("results.json", "comparison.svg")]
        },
        "visuals": [{"path": BASE + "comparison.svg",
                     "caption": "Control-qualified outcomes for six key-value distributions. Each bar represents 314,432 alphabet combinations within one bounded screen; tiny hex survivors are listed exactly in the article."}],
        "sources": [
            {"label": "Pinned Wulfic Stage V source", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_v.py"},
            {"label": "Pinned published Stage V results", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/reference/findings/stage_v_results.tsv"},
            {"label": "Pinned Quagmire model", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/lpcore/quagmire.py"}
        ],
        "related": ["wulfic-position-alphabet-flatness-bound", "quagmirror-six-rune-replay"]
    }
    (HERE / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
