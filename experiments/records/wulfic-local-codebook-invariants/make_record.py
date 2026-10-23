"""Assemble the bounded source-replay record with checked file digests."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = f"experiments/records/{HERE.name}/"


def hashed(path: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


if __name__ == "__main__":
    pages = [f"lp2-{n:02d}" for n in range(56)]
    source_tables = [f"source-stage_{stage}_{kind}.tsv"
                     for stage, kinds in (("aa", ("results", "verdicts", "controls")),
                                          ("z", ("results", "controls"))) for kind in kinds]
    inputs = ["plan.json", "check.py", "plot.py", "replay_source.py", "make_plan.py", "make_record.py"] + source_tables
    inputs = [BASE + name for name in inputs]
    inputs += ["data/index.json"] + [f"data/pages/{page}.json" for page in pages]
    record = {
        "id": HERE.name,
        "status": "draft",
        "title": "Fixed local codebooks and repeat preservation",
        "question": "Do source-defined fixed context, word and aligned-block encoders preserve more repeated units than LP2 contains?",
        "reader_question": "Could a fixed local rule have produced the sparse repeats in LP2?",
        "summary": "Exact Wulfic Stage AA/Z replay excludes short fixed contexts, repeated-word codebooks and shorter aligned-block codebooks under its controls. Longer contexts and blocks lack power for a verdict.",
        "finding": "Five of 26 local-context width cells and 26 of 72 word/block-codebook cells are excluded. The other 67 cells are unresolved by their positive controls; no LP2 cipher or plaintext is identified.",
        "limitations": "The invariant assumes a fixed position-independent local rule or fixed word/block mapping, with the source's anti-doublet redrawing model. Long contexts/blocks often have too few repeat opportunities; variable keys, state and altered boundaries remain outside scope.",
        "next_steps": "Specify a stateful or variable-key model and test its own invariant or run planted power controls before using absent repeats as evidence for or against it.",
        "outcome": "inconclusive",
        "tags": ["LP2", "source replay", "repeats", "local context", "codebook", "search bounds"],
        "scope": {
            "pages": pages,
            "artifacts": [BASE + name for name in source_tables],
            "representation": "Pinned 12,956-rune, 2,896-word LP2 section 7–15 transcription; nine sections, with within-section or joined-stream grouping; word/block equality in GP29 indices.",
            "procedure": "Replay exact Wulfic Stage AA and Z source output tables; independently reconstruct manuscript words and recount every declared LP2 repeated-unit statistic; verify control verdicts and an injective planted invariant.",
            "parameters": "AA widths 0–12, n-grams 3–7, two grouping modes; Z word comparisons and aligned blocks n=2–8 at every offset, two modes. Source seed 3301, 1,000 null draws and 200 positive draws per Emerson and LP1 source per cell, with 81% redraw of adjacent repeats.",
            "exclusions": "Position-dependent or keyed mappings, arbitrary mutable state, different section/word boundaries, corrected transcription, other sources or control distributions, and claims of plaintext recovery."
        },
        "review": {
            "kind": "exact public-source replay with independent manuscript-statistic check",
            "retested_on": "2026-10-23",
            "reviewer": "Five full source TSVs compared byte-for-byte; independent LP2 word and repeat recount; source planted controls and toy invariant",
            "human_review": "pending"
        },
        "reproduction": {
            "command": "python " + BASE + "run.py --check && python " + BASE + "check.py && python " + BASE + "plot.py --check",
            "environment": "Python 3 standard library for bundled checks. Optional full source rerun requires the pinned Wulfic checkout and its NumPy dependency.",
            "script": BASE + "run.py",
            "script_sha256": hashed(BASE + "run.py")["sha256"],
            "inputs": [hashed(name) for name in inputs],
            "outputs": [hashed(BASE + name) for name in ("results.json", "comparison.svg")]
        },
        "visuals": [{"path": BASE + "comparison.svg", "caption": "Source-controlled exclusions and unresolved cells for the fixed local-rule models."}],
        "sources": [
            {"label": "Wulfic Stage AA at pinned revision", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_aa.py"},
            {"label": "Wulfic Stage Z at pinned revision", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_z.py"},
            {"label": "Pinned source findings", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/tree/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/reference/findings"}
        ],
        "related": ["word-reset-repetition", "wulfic-stage-ab-reset-alphabets"]
    }
    (HERE / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
