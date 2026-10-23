"""Recheck archived full-output agreement from structured page JSON, not text files."""
from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT.parent / "sources/failed-attempts-d219a8"
HERE = ROOT / "research/source-intake"
W = ROOT / "experiments/records/public-wordlist-vigenere"
C = ROOT / "experiments/records/public-circumference-substitutions"
saved = json.loads((HERE / "failed-attempts-complete-output-audit.json").read_bytes())
assert subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"]).decode().strip() == saved["source_revision"]
GRID_ROW = re.compile(r"^\s*(?:[0-9A-Za-z]{2}\s+){7}[0-9A-Za-z]{2}\s*$")

RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
LABELS = ("F", "U", "TH", "O", "R", "C", "G", "W", "H", "N", "I", "J", "EO",
          "P", "X", "S", "T", "B", "E", "M", "L", "NG", "OE", "D", "A", "AE", "Y", "IA", "EA")
LOOKUP = {symbol: index for index, symbol in enumerate(RUNES)}


def source_latin(chunk: str):
    return "".join("".join(re.findall("[A-Z]+", row)) for row in chunk.splitlines()
                   if not GRID_ROW.fullmatch(row)).replace("IO", "IA")


def page_lines(number: int):
    record = json.loads((ROOT / f"data/pages/lp2-{number:02d}.json").read_bytes())
    assert record["id"] == f"lp2-{number:02d}"
    rows = [[LOOKUP[c] for c in line["raw"] if c in LOOKUP] for line in record["lines"]]
    text = (ROOT / f"text/lp2-{number:02d}.txt").read_text(encoding="utf-8")
    assert [LOOKUP[c] for c in text if c in LOOKUP] == [value for row in rows for value in row]
    return rows


def verify():
    wplan = json.loads((W / "plan.json").read_bytes())
    zip_path = SOURCE / wplan["source_archive"]
    assert hashlib.sha256(zip_path.read_bytes()).hexdigest() == saved["wordlist"]["source_zip_sha256"]
    keylist = [[LOOKUP[c] for c in item["runes"]] for item in wplan["keys"]]
    word_count = 0
    with zipfile.ZipFile(zip_path) as archive:
        for page in range(58):
            content = archive.read(f"Page{page}.txt").decode("utf-8")
            chunks = re.split(r"-{6,} ↑  [^\n]+  ↑ -{6,}", content)
            assert len(chunks) == 44
            lines = page_lines(page)
            for key_index, key in enumerate(keylist):
                result = []
                phase = 0
                for line_number, values in enumerate(lines, 1):
                    decoded = []
                    for cipher in values:
                        decoded.append(LABELS[(cipher + 29 - key[phase % len(key)]) % 29])
                        phase += 1
                    result.extend(decoded)
                output = "".join(result).replace("IO", "IA")
                assert output == source_latin(chunks[key_index]), (page, key_index)
                word_count += 1
    assert word_count == saved["wordlist"]["complete_matches"] == 2494

    cplan = json.loads((C / "plan.json").read_bytes())
    prime = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
             53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109)
    for radius, source_item in zip(("index", "prime"), cplan["source_outputs"]):
        path = SOURCE / source_item["path"]
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == saved["circumference"][radius]["source_git_blob_sha256"]
        assert hashlib.sha256(raw.replace(b"\n", b"\r\n")).hexdigest() == source_item["sha256"]
        chunks = re.split(r"-{6,} ↓  Page \d+  ↓ -{6,}", raw.decode("utf-8"))
        assert len(chunks) == 58
        radii = range(29) if radius == "index" else prime
        translation = [math.floor(2 * math.pi * value) % 29 for value in radii]
        hits = 0
        for page in range(57):
            lines = page_lines(page)
            displayed = "".join(LABELS[translation[value]]
                                for line_number, line in enumerate(lines, 1)
                                for value in line).replace("IO", "IA")
            assert displayed == source_latin(chunks[page + 1]), (radius, page)
            hits += 1
        assert hits == saved["circumference"][radius]["complete_matches"] == 57
    assert saved["published_unsolved_scope"]["wordlist"]["complete_matches"] == 2408
    assert all(saved["published_unsolved_scope"]["circumference"][radius]["complete_matches"] == 56
               for radius in ("index", "prime"))
    print("PASS: all 2,494 wordlist and both 57-page circumference archived outputs match completely")


if __name__ == "__main__":
    verify()
