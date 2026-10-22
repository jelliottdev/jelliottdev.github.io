"""Measure how the five seventh-onion grid variants affect published grid analyses.

This compares two saved transcriptions, not a visually certified correction.
Run with --check to verify the published report against its pinned inputs.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRID = ROOT / "exports/alphanumeric-grids.json"
VARIANTS = ROOT / "exports/seventh-onion-grid-variants.csv"
PATHS = [ROOT / "exports/grid-prime-paths.json",
         ROOT / "experiments/records/grid-prime-paths-page-boundaries/results.json"]
OUTPUT = ROOT / "exports/grid-source-sensitivity.json"
DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def byte(token):
    result = 60 * DIGITS.index(token[0]) + DIGITS.index(token[1])
    if not 0 <= result <= 255:
        raise ValueError(f"Not a byte under the declared interpretation: {token}")
    return result


def key(cell):
    return cell["page"], int(cell["row"]), int(cell["column"])


def report():
    raw_grid, raw_variants = GRID.read_bytes(), VARIANTS.read_bytes()
    rows = json.loads(raw_grid)["records"]
    variants = list(csv.DictReader(raw_variants.decode("utf-8").splitlines()))
    if len(rows) != 256 or len(variants) != 5:
        raise ValueError("Unexpected grid or source-variant size")
    wiki = {key(cell): cell["token"] for cell in rows}
    archive = dict(wiki)
    details = []
    for item in variants:
        cell = key(item)
        if wiki[cell] != item["wiki_token"]:
            raise ValueError(f"Variant disagrees with grid export at {cell}")
        archive[cell] = item["archive_token"]
        old, new = byte(item["archive_token"]), byte(item["wiki_token"])
        details.append({"page": cell[0], "row": cell[1], "column": cell[2],
                        "archive_token": item["archive_token"], "wiki_token": item["wiki_token"],
                        "archive_byte": old, "wiki_byte": new,
                        "differing_bits": (old ^ new).bit_count()})
    ordered = [key(cell) for cell in rows]
    first_characters_identical = all(archive[cell][0] == wiki[cell][0] for cell in ordered)
    if not first_characters_identical:
        raise ValueError("Prefix-based prime-path counts may differ")
    streams = {}
    for name, values in (("archive", archive), ("wiki", wiki)):
        data = bytes(byte(values[cell]) for cell in ordered)
        streams[name] = {"byte_stream_sha256": sha256(data), "value_sum": sum(data),
                         "distinct_values": len(set(data))}
    paths = []
    for source in PATHS:
        source_bytes = source.read_bytes()
        result = json.loads(source_bytes)
        touched = []
        for index, hit in enumerate(result["hits"], 1):
            cells = [key(cell) for cell in hit["cells"]]
            wiki_suffix = "".join(wiki[cell][1] for cell in cells)
            archive_suffix = "".join(archive[cell][1] for cell in cells)
            if wiki_suffix != hit["suffixes"]:
                raise ValueError(f"Published hit suffix disagrees with wiki grid: {source} #{index}")
            if archive_suffix != wiki_suffix:
                touched.append({"hit_ordinal": index, "digits": hit["digits"],
                                "wiki_suffix": wiki_suffix, "archive_suffix": archive_suffix,
                                "variant_cells": [list(cell) for cell in cells if archive[cell] != wiki[cell]]})
        paths.append({"source": source.relative_to(ROOT).as_posix(),
                      "source_sha256": sha256(source_bytes), "published_prime_occurrences": len(result["hits"]),
                      "prime_occurrences_invariant": first_characters_identical,
                      "hits_with_changed_suffix": len(touched), "changed_hits": touched})
    return {"schema": "liberpedia-grid-source-sensitivity-v1",
            "scope": "Two preserved transcriptions at five differing cells; no exhaustive image-glyph review.",
            "sources": {"grid": {"path": GRID.relative_to(ROOT).as_posix(), "sha256": sha256(raw_grid)},
                        "variants": {"path": VARIANTS.relative_to(ROOT).as_posix(), "sha256": sha256(raw_variants)}},
            "base60_rule": "0-9 A-Z a-x = 0-59; token xy = 60*index(x)+index(y). This is a conditional representation, not a cipher solution.",
            "variant_cells": details, "differing_bytes": len(details),
            "differing_bits_total": sum(cell["differing_bits"] for cell in details),
            "first_characters_identical": first_characters_identical,
            "byte_streams": streams, "prime_path_reports": paths,
            "limits": "Only recorded archive-versus-wiki differences are varied. Other visually ambiguous stems may exist. Unchanged prime-path counts do not make suffix strings or base-60 bytes stable."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = (json.dumps(report(), indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if args.check:
        if OUTPUT.read_bytes() != output:
            raise SystemExit("Published sensitivity report differs from the source audit")
        print("PASS: five byte variants and both prime-path suffix audits reproduce")
    elif args.write:
        OUTPUT.write_bytes(output)
        print("Wrote", OUTPUT.relative_to(ROOT))
    else:
        print(output.decode("utf-8"), end="")
