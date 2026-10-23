"""Freeze pinned source-page text and source scoring constants before scoring."""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import argparse

HERE = pathlib.Path(__file__).resolve().parent
PAGES = [28, 15, 20, 21, 22, 27, 29, 30, 40, 41, 42, 43]


def git_bytes(source_root: pathlib.Path, path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(source_root), "show", "HEAD:" + path])


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", type=pathlib.Path, required=True)
    ap.add_argument("--liberpedia-root", type=pathlib.Path, default=HERE.parents[2])
    args = ap.parse_args()
    source = git_bytes(args.source_root, "tools/legacy/lfsr_alberti_solver.py")
    assert digest(source) == "4bdabdcf326b90a9f89f4165414e9eaa5dd653a934a1bcd2a484e786f6dac815"
    env = {"__name__": "source_module"}
    exec(compile(source, "pinned lfsr_alberti_solver.py", "exec"), env)
    pages = []
    for ordinal in PAGES:
        raw = git_bytes(args.source_root, f"pages/page_{ordinal:02d}/runes.txt")
        pages.append({
            "source_ordinal": ordinal,
            "manuscript_page": f"lp1-{ordinal:02d}" if ordinal < 17 else f"lp2-{ordinal-17:02d}",
            "sha256": digest(raw),
            "text": raw.decode("utf-8"),
        })
    known_path = args.liberpedia_root / "data/evidence/known-readings.json"
    known_blob = known_path.read_bytes()
    known = json.loads(known_blob)
    wanted = {"welcome", "first-koan", "loss-of-divinity", "second-koan"}
    readings = []
    for row in known["controls"]:
        if row["id"] in wanted:
            indices = [v for page in row["decoded_pages"] for v in page["rune_indices"]][:250]
            assert len(indices) == 250
            readings.append({"id": row["id"], "first_250": indices})
    assert {r["id"] for r in readings} == wanted
    inputs = {
        "schema": "wulfic-separator-clock-inputs-v1",
        "source_sha256": digest(source),
        "known_readings_sha256": digest(known_blob),
        "source_literal_runes": "".join(env["RUNES"]),
        "canonical_runes": "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ",
        "separators": "".join(sorted(env["SEPARATORS"])),
        "bigrams": [[a, b, value] for (a, b), value in sorted(env["COMMON_BIGRAMS"].items())],
        "trigrams": [list(row) for row in sorted(env["COMMON_TRIGRAMS_SET"])],
        "readings": readings,
        "pages": pages,
    }
    (HERE / "inputs.json").write_text(json.dumps(inputs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("saved", len(pages), "pages,", len(readings), "positive readings")


if __name__ == "__main__":
    main()
