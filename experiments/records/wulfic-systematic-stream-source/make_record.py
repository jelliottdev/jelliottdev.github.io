"""Write manifest hashes for the frozen grouped source replay."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREFIX = "experiments/records/wulfic-systematic-stream-source/"


def item(name: str) -> dict:
    path = HERE / name
    return {"path": PREFIX + name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def build() -> dict:
    return {
      "id": "wulfic-systematic-stream-source",
      "status": "draft",
      "title": "Prime streams and a short feedback key",
      "question": "Do the exact executed prime-derived and two-value feedback searches in archived stream_cipher_attack.py provide a distinctive LP2 reading under the source's own score?",
      "reader_question": "Could a prime sequence or short feedback key decode these pages?",
      "summary": "The full pinned source searches produce many threshold hits, but complete searches on 19 shuffled versions do too. The score does not establish a reading.",
      "finding": "On 38 matched LP2 pages, 2,964 prime-stream settings yielded 644 source-threshold hits (19 shuffled-search range 625–702). On three selected pages, all 6,365,529 two-value LFSR settings yielded 38,826 hits (shuffled range 33,694–44,833). The best stream IoC 1.140 was reached or exceeded by 16/19 controls; the best LFSR combined score was reached or exceeded by 11/19.",
      "limitations": "The source's IoC/bigram/I-or-A-singleton score is a permissive candidate screen, not a reading test. Nineteen within-page shuffles supply only a coarse descriptive selection control and are not a cipher model. Old source page labels actually select LP2-01–38; the source-defined but uncalled Fibonacci stream and unfinished Berlekamp–Massey reconstruction are excluded. Other generator lengths, feedback clocks and page ranges remain open.",
      "next_steps": "Specify a key rule that predicts a longer passage or untouched page before selecting another score peak.",
      "outcome": "inconclusive",
      "tags": ["LP2", "source replay", "prime streams", "LFSR", "selection effect", "index of coincidence"],
      "scope": {
        "pages": [f"lp2-{i:02d}" for i in range(1, 39)],
        "artifacts": [PREFIX + "plan.json", PREFIX + "inputs.json"],
        "representation": "Pinned source Git-object rune text using its exact GP29 alphabet and period/hyphen/bullet/space/newline word separators. Source page_18..55 maps to current LP2-01..38; separate LFSR selection is LP2-28,10,17.",
        "procedure": "Run every entry of the source's 26-stream dictionary in three modes over every eligible source page. Run all 29^4 ordered two-value LFSR state/tap tuples in three modes over the three highest-singleton pages, including zero/singular tap cases. Preserve the source IoC, bigram and I/A singleton score and hit thresholds. Repeat the entire selected grids on 19 within-page rune shuffles.",
        "parameters": "2,964 stream page-settings; 6,365,529 LFSR page-settings; source thresholds combined>2 or IoC>1.5 for streams, combined>3 for LFSR; shuffle seed 20261023.",
        "exclusions": "Uncalled Fibonacci generator, incomplete Berlekamp–Massey key reconstruction, pages outside source selection, other prime rules, longer/nonlinear feedback or different alphabet/language models."
      },
      "review": {"kind": "complete corrected-input source grid with source-function parity and selected-search controls",
                 "retested_on": "2026-10-23",
                 "reviewer": "All 26 generators and 107 zero-inclusive LFSR tuples matched pinned source functions before scoring; planted full-page recovery passed. Independent scalar checks verify all retained winners and a complete shuffled LFSR search.",
                 "human_review": "pending"},
      "reproduction": {
        "command": "python experiments/records/wulfic-systematic-stream-source/check.py && python experiments/records/wulfic-systematic-stream-source/plot.py --check",
        "environment": "Python 3 with NumPy and Numba. run.py --check repeats the entire search and 19 controls. Optional gate.py and snapshot_inputs.py --source-root PATH --check compare with a checkout of the pinned Wulfic Git revision.",
        "script": PREFIX + "check.py",
        "script_sha256": item("check.py")["sha256"],
        "inputs": [item(name) for name in ("plan.json", "inputs.json", "snapshot_inputs.py", "engine.py", "gate.py", "run.py", "check.py", "plot.py", "make_record.py", "article.md")],
        "outputs": [item(name) for name in ("gate.json", "results.json", "comparison.svg")]
      },
      "visuals": [{"path": PREFIX + "comparison.svg", "caption": "The manuscript's source-threshold hit counts fall inside the range from 19 complete searches on shuffled page runes."}],
      "sources": [{"label": "Pinned archived stream cipher source", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/stream_cipher_attack.py"},
                  {"label": "Archived legacy warning", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/README.md"}],
      "related": ["wulfic-prime-keyword-stream-families", "wulfic-lfsr-singleton-constraints", "wulfic-keyword-prime-layer-grid"]
    }


def main() -> None:
    output = json.dumps(build(), ensure_ascii=False, indent=2).encode("utf8") + b"\n"
    (HERE / "record.json").write_bytes(output)
    print(f"Record manifest written ({len(output)} bytes).")


if __name__ == "__main__":
    main()
