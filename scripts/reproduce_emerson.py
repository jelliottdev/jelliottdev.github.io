"""Replay the known 2014 entrance coordinates against a frozen PDF derivative.

Default: Python standard library only; print a lookup trace without writing.
--check-pdf: additionally re-extract the pinned PDF using pypdf 6.19.0 and
compare every derived paragraph. No network access or hidden-service requests.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import string
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
SOURCE_HASH = "fee032e9ff4f2429fccc120831f9ad7a6d27d36f70828f037c191d5f34900abd"


def extract_pdf():
    import pypdf
    if pypdf.__version__ != "6.19.0":
        raise ValueError("Exact PDF replay requires pypdf 6.19.0")
    path = ROOT / "exports/sources/emerson-self-reliance.pdf"
    if hashlib.sha256(path.read_bytes()).hexdigest() != SOURCE_HASH:
        raise ValueError("PDF differs from the source snapshot")
    paragraphs = []
    active = False
    for page_number, page in enumerate(pypdf.PdfReader(path).pages, 1):
        for line in page.extract_text(extraction_mode="layout").splitlines():
            if not line.strip() or re.fullmatch(r"\s*\d+\s*", line):
                continue
            if "I read the other day" in line:
                active = True
            if not active:
                continue
            indent = len(line) - len(line.lstrip())
            text = unicodedata.normalize("NFKC", line.strip())
            # Four-space prose indentation starts a paragraph. The seven-space
            # verse on printed page 16 remains in its surrounding paragraph.
            if indent == 4:
                paragraphs.append({"printed_page": page_number, "text": text})
            elif paragraphs:
                joiner = "" if paragraphs[-1]["text"].endswith("-") else " "
                paragraphs[-1]["text"] += joiner + text
            else:
                raise ValueError("First prose paragraph was not recognized")
    if len(paragraphs) != 50:
        raise ValueError("Expected 50 prose paragraphs")
    return paragraphs


def replay(paragraphs, entries):
    trace = []
    for entry in entries:
        if ":" not in entry:
            if len(entry) != 1:
                raise ValueError("Literal must be a single character")
            trace.append({"entry": entry, "literal": True, "character": entry})
            continue
        coordinates = list(map(int, entry.split(":")))
        if len(coordinates) != 4 or min(coordinates) < 1:
            raise ValueError("Coordinates must be four positive integers")
        p, s, w, letter = coordinates
        try:
            paragraph = paragraphs[p - 1]
            sentences = [part.strip() for part in
                         re.split(r"[.!?]+", paragraph["text"]) if part.strip()]
            sentence = sentences[s - 1]
            words = [part.strip(string.punctuation + "“”‘’")
                     for part in sentence.split()]
            word = [part for part in words if part][w - 1]
            letters = re.sub(r"[^A-Za-z]", "", word)
            character = letters[letter - 1]
        except IndexError as error:
            raise ValueError(f"Coordinate out of range: {entry}") from error
        trace.append({"entry": entry, "printed_page": paragraph["printed_page"],
                      "sentence": sentence, "word": word, "character": character})
    return {"decoded": "".join(row["character"] for row in trace), "trace": trace}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-pdf", action="store_true")
    args = parser.parse_args()
    evidence = json.loads((ROOT / "data/evidence/emerson-book-cipher.json")
                          .read_text(encoding="utf-8"))
    body = (ROOT / evidence["coordinate_payload_path"]).read_bytes()
    if hashlib.sha256(body).hexdigest() != evidence["coordinate_payload_sha256"]:
        raise ValueError("Coordinate message checksum mismatch")
    lines = body.decode("ascii").splitlines()
    start = next(i for i, line in enumerate(lines)
                 if re.fullmatch(r"\d+:\d+:\d+:\d+", line))
    entries = []
    for line in lines[start:]:
        if line == "Good luck.":
            break
        if line.strip():
            entries.append(line)
    if entries != evidence["entries"]:
        raise ValueError("Coordinates differ from the extracted message")
    source = ROOT / evidence["paragraphs_path"]
    if hashlib.sha256(source.read_bytes()).hexdigest() != evidence["paragraphs_sha256"]:
        raise ValueError("Paragraph derivative checksum mismatch")
    paragraphs = json.loads(source.read_text(encoding="utf-8"))
    if args.check_pdf and extract_pdf() != paragraphs:
        raise ValueError("PDF extraction differs from the published paragraphs")
    result = replay(paragraphs, entries)
    if result != evidence["result"]:
        raise ValueError("Lookup trace differs from the recorded control")
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
