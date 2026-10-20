"""Reproduce the 2012 second-chance book code; print JSON to stdout.
Run from any directory: python scripts/reproduce_second_chance.py
Uses only the Python standard library. No network access or historical URL visits.
"""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "exports/sources/second-chance-voice-of-devil.txt"
PAYLOAD = "exports/steganography/second-chance-2012.outguess.bin"

def checked(path, expected):
    raw = (ROOT / path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected:
        raise ValueError(f"Input checksum mismatch: {path}")
    return raw.decode("utf-8"), digest

def reproduce():
    source, source_hash = checked(SOURCE, "9f40dfca4c98544323db16289289580278ce757790c64bf09b73d76d0ede64ae")
    payload, payload_hash = checked(PAYLOAD, "82b49ba4fe46ac32a80382ccd49d49f29371b787bc84409378ff25e2d45729cc")
    raw_lines = source.splitlines()
    if raw_lines[:3] != ["The voice of the", "Devil", ""]:
        raise ValueError("Unexpected source heading")
    # Preserve printed body line breaks. Indentation is not counted.
    lines = [line.strip() for line in raw_lines[3:]
             if line.strip() and not line.startswith("//")]
    signed_body = payload.split("-----BEGIN PGP SIGNATURE-----", 1)[0]
    pairs = re.findall(r"^(\d+):(\d+)\r?$", signed_body, re.MULTILINE)
    if len(lines) != 18 or len(pairs) != 22:
        raise ValueError("Unexpected source or coordinate count")
    trace = []
    for position, (row, column) in enumerate(pairs, 1):
        row, column = int(row), int(column)
        if not 1 <= row <= len(lines) or not 1 <= column <= len(lines[row - 1]):
            raise ValueError("Coordinate outside source")
        trace.append(dict(position=position, line=row, column=column,
                          character=lines[row - 1][column - 1], source_line=lines[row - 1]))
    return dict(source_path=SOURCE, source_sha256=source_hash,
                source_url="https://connortumbleson.com/uploads/2021/04/voice_of_devil.txt",
                payload_path=PAYLOAD, payload_sha256=payload_hash,
                convention="One-based line and character; omit title, blank lines and source comment; trim indentation; retain internal spaces, punctuation, paragraph numbers and line-end hyphen.",
                lines=lines, trace=trace,
                result="".join(item["character"] for item in trace),
                scope="Historical book-code reproduction using an attributed transcription; not a new Liber Primus solution or a signature verification.")

if __name__ == "__main__":
    print(json.dumps(reproduce(), indent=2, ensure_ascii=False))
