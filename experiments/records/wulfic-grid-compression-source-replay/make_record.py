"""Refresh Stage X4 component draft metadata and file hashes."""
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
    assert result["decoder_tests"] == 20 and result["decoder_eof"] == 0
    assert result["calibration_eof_hits"] == {
        "zlib raw deflate": 552, "zlib": 0, "gzip": 0, "bz2": 0, "lzma auto": 0}
    inputs = [BASE + x for x in ("plan.json", "check.py", "plot.py", "replay_source.py",
                                  "make_record.py", "source-stage_x4_rows.tsv")]
    record = {
        "id": HERE.name, "status": "draft",
        "title": "Complete-stream decompression of the LP2 number grid",
        "question": "Do the printed number-grid bytes form a complete raw DEFLATE, zlib, gzip, bzip2 or LZMA stream in any of four fixed routes?",
        "reader_question": "Does the number grid decompress as a complete stream?",
        "summary": "Exact Wulfic Stage X4 component replay and an independent checker find no end-of-stream across five decoders and four full-grid routes.",
        "finding": "Zero of 20 complete-grid decoder calls reaches EOF. All 24 pinned X4 rows reproduce exactly, including four absent offset-zero signature rows. The source's 100,000-block calibration yielded 552 raw-DEFLATE EOFs and zero observed for each other decoder; independent recomputation matches. Synthetic complete/truncated/trailing-junk controls pass as separately labeled post-replay diagnostics.",
        "limitations": "Only 256 exact printed-grid bytes, four source routes, five decoder APIs, offset zero, a single call and 1 MiB output cap. Source EOF does not require consuming all input; zero calibration hits is finite-sample evidence, not a true zero rate. Other byte constructions, offsets, keys, formats and larger outputs remain untested.",
        "next_steps": "A compression proposal should specify the grid bytes, route, exact codec and any pre-transform before testing, then validate a complete output and trailing-input rule.",
        "outcome": "not-supported",
        "tags": ["LP2", "number grid", "source replay", "compression", "raw DEFLATE", "full stream"],
        "scope": {
            "pages": ["lp2-49", "lp2-50", "lp2-51"],
            "artifacts": [BASE + "source-stage_x4_rows.tsv"],
            "representation": "The 256 printed base-60 grid cells parsed to bytes in row/reversed-row/column/reversed-column order.",
            "procedure": "Replay the pinned Stage X4 component with 100,000 seeded uniform-byte calibration blocks for each decoder. Test each complete grid route with raw DEFLATE, zlib, gzip, bzip2 and LZMA; also preserve Stage N offset-zero signature rows. Independently reconstruct the grid and every decoder result.",
            "parameters": "Five source decoders × four routes = 20 complete-stream calls, plus four signature checks. One bounded call per decoder with 1 MiB output cap; source PASS requires EOF and empirical null rate ×20≤0.01.",
            "exclusions": "Nonzero offsets, prefixes, modified grid cells, keys or other transformations, other compression formats, full-input-consumption requirement and larger decompressed outputs."
        },
        "review": {
            "kind": "exact public-source Stage X4 component replay with independent decoder and null checks",
            "retested_on": "2026-10-23",
            "reviewer": "All 24 X4 rows matched pinned Stage X result subset; site grid rebuilt independently and all 500,000 decoder-calibration calls reproduced; later synthetic controls explicitly separated",
            "human_review": "pending"
        },
        "reproduction": {
            "command": f"python {BASE}run.py --check && python {BASE}plot.py --check",
            "environment": "Python 3 standard library and NumPy. Optional external-source replay requires the pinned Wulfic checkout.",
            "script": BASE + "run.py", "script_sha256": hashed(BASE + "run.py")["sha256"],
            "inputs": [hashed(x) for x in inputs],
            "outputs": [hashed(BASE + x) for x in ("results.json", "decoder-screen.svg")]
        },
        "visuals": [{"path": BASE + "decoder-screen.svg",
                     "caption": "Five complete-stream decoders on four fixed grid routes. No call reaches decoder EOF; random raw DEFLATE can reach EOF and is calibrated separately."}],
        "sources": [
            {"label": "Pinned Wulfic Stage X source", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_x.py"},
            {"label": "Pinned published Stage X result table", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/reference/findings/stage_x_other.tsv"}
        ],
        "related": ["wulfic-grid-periodic-byte-invariant", "grid-direct-bytes", "rune-direct-compression"]
    }
    (HERE / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
