#!/usr/bin/env python3
"""Freeze the finite, local LP2-56 artifact-hash inputs before computing matches."""
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PAYLOAD = "experiments/records/rsa-window-54-source-replay/source/payload_resolved.bin"


def file_entry(path):
    data = (ROOT / path).read_bytes()
    return {"path": path, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}


def target_from_page(page):
    rows = [line.rstrip("/") for line in page["reading"]["literal"].splitlines()
            if re.fullmatch(r"[0-9a-f]+/?", line)]
    target = "".join(rows)
    assert len(rows) == 5 and len(target) == 128
    return target


def main():
    pages = sorted(ROOT.glob("data/pages/lp*.json"))
    assert len(pages) == 75
    page_rows = []
    sections = defaultdict(list)
    for path in pages:
        page = json.loads(path.read_text(encoding="utf-8"))
        pid = page["id"]
        assert path.stem == pid
        image = f"images/{pid}.jpg"
        image_info = file_entry(image)
        assert image_info["sha256"] == page["image_sha256"]
        page_rows.append({"id": pid, "page": file_entry(f"data/pages/{pid}.json"),
                          "image": image_info})
        if page.get("reading") and page["reading"].get("section"):
            sections[page["reading"]["section"]].append(pid)
    assert len(sections) == 9
    assert sum(bool(json.loads((ROOT / p["page"]["path"]).read_text(encoding="utf-8"))["raw"])
               for p in page_rows) == 73
    target_page = json.loads((ROOT / "data/pages/lp2-56.json").read_text(encoding="utf-8"))
    plan = {
        "schema": "liberpedia-lp2-56-artifact-hash-plan-v1",
        "question": "Do these exact preserved Liberpedia artifact bytes equal the printed LP2-56 target under three declared 512-bit digest algorithms?",
        "target": {"hex": target_from_page(target_page), "page": "lp2-56",
                   "source": "data/pages/lp2-56.json#reading.literal", "bits": 512},
        "algorithms": ["sha512", "sha3_512", "blake2b_512"],
        "algorithm_controls": "abc vectors from standard implementations, asserted in both run.py and check.py",
        "excluded_algorithms": {"whirlpool": "Unavailable in local hashlib; not run",
                                "streebog": "Unavailable in local hashlib; not run"},
        "text_variants": [
            {"id": "exact", "rule": "UTF-8 encode the stored Unicode text exactly"},
            {"id": "crlf", "rule": "replace each LF with CRLF, then UTF-8 encode"},
            {"id": "drop-final-lf", "rule": "remove one terminal LF if present, then UTF-8 encode"},
            {"id": "one-final-lf", "rule": "strip terminal CR/LF characters and append exactly one LF, then UTF-8 encode"}
        ],
        "families": {
            "image-original": "75 existing images/lp*.jpg files, exact JPEG bytes only",
            "page-raw": "75 data/pages/lp*.json raw strings, UTF-8; two cover pages have an empty raw string",
            "section-literal": "Nine reading.section groups; concatenate stored reading.literal strings in ascending page-ID order, preserving all printed separators and page wrap",
            "grid-payload": "One 256-byte resolved payload, exact bytes only"
        },
        "pages": page_rows,
        "sections": [{"id": sid, "pages": ids} for sid, ids in sorted(sections.items())],
        "payload": file_entry(PAYLOAD),
        "source_prior": "research/failed-attempts-inventory.json#deepweb-hash-against-jpegs reports 75 JPEG hashes under SHA-512/BLAKE2, but source JPEG bytes were absent from that Git tree; this manifest uses Liberpedia's independently preserved originals.",
        "noncoverage": "No URL fetches, HTML response bodies, unknown pages, arbitrary case/encoding permutations, or digest-as-address conversions. A mismatch is scoped to the exact bytes and algorithms listed here."
    }
    out = HERE / "plan.json"
    if out.exists():
        raise SystemExit("plan.json already exists; do not silently replace a frozen plan")
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Frozen {len(page_rows)} images + 75 raw texts + {len(sections)} literal sections + one payload")


if __name__ == "__main__":
    main()
