"""Compare complete GP rune streams with every pinned Failed-Attempts output."""
from __future__ import annotations

import hashlib
import difflib
import json
import math
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT.parent / "sources/failed-attempts-d219a8"
REVISION = "d219a8099f8d24e52496e9ee3456ed9980893884"
assert subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"]).decode().strip() == REVISION
HERE = ROOT / "research/source-intake"
W = ROOT / "experiments/records/public-wordlist-vigenere"
C = ROOT / "experiments/records/public-circumference-substitutions"
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
LABELS = ("F", "U", "TH", "O", "R", "C", "G", "W", "H", "N", "I", "J", "EO",
          "P", "X", "S", "T", "B", "E", "M", "L", "NG", "OE", "D", "A", "AE", "Y", "IA", "EA")
GRID_ROW = re.compile(r"^\s*(?:[0-9A-Za-z]{2}\s+){7}[0-9A-Za-z]{2}\s*$")
def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def latin_stream(chunk: str):
    """Keep displayed Latin labels without inventing rune boundaries.

    GP labels are not prefix-free (TH may also be T+H, and so on), so greedy
    re-tokenization would create false mismatches. The archived IA/IO spelling
    for one rune is normalized on both sides at the character-string level.
    """
    words = []
    for line in chunk.splitlines():
        if GRID_ROW.fullmatch(line):
            continue
        # Decimal material may sit *inside a rune line* (for example the 7
        # on LP2-10), or label a line. Exclude only the separately structured
        # eight-cell alphanumeric grid rows; retain other mixed lines.
        words.extend(re.findall(r"[A-Z]+", line))
    return "".join(words).replace("IO", "IA")


def compare_rows(expected: str, measured: str, page: int, case: str):
    mismatch = next((i for i, (a, b) in enumerate(zip(expected, measured)) if a != b), None)
    if mismatch is None and len(expected) != len(measured):
        mismatch = min(len(expected), len(measured))
    entry = {"page": f"lp2-{page:02d}", "case": case,
             "expected_latin_chars": len(expected), "archived_latin_chars": len(measured),
             "first_mismatch_char_0based": mismatch}
    if mismatch is not None:
        edits = [op for op in difflib.SequenceMatcher(None, expected, measured, autojunk=False).get_opcodes()
                 if op[0] != "equal"]
        entry["first_edits"] = [{"operation": kind,
                                  "expected_at": i, "archive_at": j,
                                  "expected": expected[i:i_end], "archive": measured[j:j_end]}
                                 for kind, i, i_end, j, j_end in edits[:3]]
        entry["edit_count"] = len(edits)
    return entry


def wordlist():
    plan = json.loads((W / "plan.json").read_bytes())
    archive = SOURCE / plan["source_archive"]
    assert sha(archive) == plan["source_archive_sha256"]
    keys = [[RUNES.index(x) for x in item["runes"]] for item in plan["keys"]]
    rows = []
    with zipfile.ZipFile(archive) as zipfile_in:
        for page in range(58):
            content = zipfile_in.read(f"Page{page}.txt").decode("utf-8")
            chunks = re.split(r"-{6,} ↑  [^\n]+  ↑ -{6,}", content)
            assert len(chunks) == 44
            raw = (ROOT / f"text/lp2-{page:02d}.txt").read_text(encoding="utf-8")
            cipher = [RUNES.index(x) for x in raw if x in RUNES]
            for k, key in enumerate(keys):
                expected = "".join(LABELS[(c - key[i % len(key)]) % 29]
                                   for i, c in enumerate(cipher)).replace("IO", "IA")
                measured = latin_stream(chunks[k])
                rows.append(compare_rows(expected, measured, page, f"key-{k+1:02d}"))
    return {"source_zip_sha256": sha(archive), "cases": rows}


PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
          53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109)


def circumference():
    plan = json.loads((C / "plan.json").read_bytes())
    output = {}
    for radius, source in zip(("index", "prime"), plan["source_outputs"]):
        path = SOURCE / source["path"]
        raw_bytes = path.read_bytes()
        # The published record pinned Windows checkout CRLF bytes. The pinned
        # Git blob and this clone use LF; verify the exact newline relationship.
        assert hashlib.sha256(raw_bytes.replace(b"\n", b"\r\n")).hexdigest() == source["sha256"]
        content = path.read_text(encoding="utf-8")
        chunks = re.split(r"-{6,} ↓  Page \d+  ↓ -{6,}", content)
        assert len(chunks) == 58
        radii = range(29) if radius == "index" else PRIMES
        table = [math.trunc(2 * math.pi * r) % 29 for r in radii]
        cases = []
        for page in range(57):
            raw = (ROOT / f"text/lp2-{page:02d}.txt").read_text(encoding="utf-8")
            expected = "".join(LABELS[table[RUNES.index(x)]]
                               for x in raw if x in RUNES).replace("IO", "IA")
            measured = latin_stream(chunks[page + 1])
            cases.append(compare_rows(expected, measured, page, radius + "-truncate"))
        output[radius] = {"source_git_blob_sha256": sha(path),
                          "prior_record_crlf_sha256": source["sha256"], "cases": cases}
    return output


def summarize(rows):
    mismatches = [x for x in rows if x["first_mismatch_char_0based"] is not None]
    return {"case_count": len(rows), "complete_matches": len(rows) - len(mismatches),
            "mismatches": len(mismatches),
            "first_mismatches": mismatches[:20]}


if __name__ == "__main__":
    w = wordlist()
    c = circumference()
    result = {
        "schema": "liberpedia-failed-attempts-complete-output-audit-v1",
        "source_revision": REVISION,
        "input_rule": "Compare complete concatenated GP Latin label strings; exclude only eight-cell alphanumeric grid rows, remove nonletters elsewhere (including embedded digits), and normalize IA/IO alias on both sides. Rune labels are not prefix-free, so no greedy inverse tokenization is used.",
        "wordlist": {"source_zip_sha256": w["source_zip_sha256"], **summarize(w["cases"]), "cases": w["cases"]},
        "circumference": {radius: {"source_git_blob_sha256": part["source_git_blob_sha256"],
                                     "prior_record_crlf_sha256": part["prior_record_crlf_sha256"],
                                     **summarize(part["cases"]), "cases": part["cases"]} for radius, part in c.items()}
    }
    result["published_unsolved_scope"] = {
        "wordlist": summarize([x for x in w["cases"] if int(x["page"][-2:]) <= 55]),
        "circumference": {radius: summarize([x for x in part["cases"] if int(x["page"][-2:]) <= 55])
                          for radius, part in c.items()}}
    path = HERE / "failed-attempts-complete-output-audit.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"wordlist": {k: result["wordlist"][k] for k in ("case_count", "complete_matches", "mismatches")},
                      "circumference": {radius: {k: result["circumference"][radius][k] for k in ("case_count", "complete_matches", "mismatches")} for radius in c}}, indent=2))
