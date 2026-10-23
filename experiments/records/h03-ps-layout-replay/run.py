#!/usr/bin/env python3
"""Independent 2012 P.S. layout replay of pinned round28/L5 H-03r."""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source"
RNG = random.Random(13301)
CONSTANTS = (
    "1325734783", "845145127", "1231507051321",
    "10412790658919985359827898739594318956404425106955675643739226952372682423852959081739834390370374475764863415203423499357108713631",
)


def primary_lines() -> list[str]:
    raw = (SOURCE / "ky_2012-01-final-message.asc").read_text(encoding="utf-8")
    message = raw.split("-----BEGIN PGP SIGNATURE-----", 1)[0]
    first = message.find("P.S. ")
    if first < 0:
        raise ValueError("No P.S. block in pinned 2012 signed-message text")
    relevant = message[first:].splitlines()
    first_digits = relevant[0].split("P.S. ", 1)[1].rstrip("\\").strip()
    lines = [first_digits, relevant[1].strip().rstrip("\\"), relevant[2].strip()]
    if [len(line) for line in lines] != [40, 45, 46] or not all(line.isdecimal() for line in lines):
        raise ValueError("Unexpected 2012 P.S. physical lines")
    return lines


def routes(lines: list[str], indent: int = 0) -> dict[str, str]:
    if indent:
        rows = ["." * indent + lines[0], *lines[1:]]
    else:
        rows = lines
    width = max(map(len, rows))
    output = {}
    for col_direction, row_direction, name in (
        (1, 1, "cols_L2R_top2bot"), (1, -1, "cols_L2R_bot2top"),
        (-1, 1, "cols_R2L_top2bot"), (-1, -1, "cols_R2L_bot2top"),
    ):
        columns = range(width) if col_direction == 1 else range(width - 1, -1, -1)
        ordered_rows = rows if row_direction == 1 else list(reversed(rows))
        output[name] = "".join(row[c] for c in columns for row in ordered_rows
                               if c < len(row) and row[c].isdigit())
    if indent == 0:
        output["concat_fwd"] = "".join(lines)
        output["concat_rev"] = output["concat_fwd"][::-1]
    return output


def printable_pair_score(digits: str) -> tuple[float, int, int, str]:
    best = (-1.0, 0, 0, "")
    for alignment in (0, 1):
        values = [int(digits[i:i + 2]) for i in range(alignment, len(digits) - 1, 2)]
        printable = sum(32 <= value <= 126 for value in values)
        score = printable / len(values)
        shown = "".join(chr(value) if 32 <= value <= 126 else "." for value in values)
        if score > best[0]:
            best = (score, alignment, printable, shown)
    return best


def composite_witness(value: int) -> int | None:
    """A returned witness proves compositeness; None means only probable prime."""
    if value < 2:
        return 2
    for small in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if value == small:
            return None
        if value % small == 0:
            return small
    odd = value - 1
    power = 0
    while odd % 2 == 0:
        odd //= 2
        power += 1
    for base in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43):
        residue = pow(base, odd, value)
        if residue in (1, value - 1):
            continue
        for _ in range(power - 1):
            residue = residue * residue % value
            if residue == value - 1:
                break
        else:
            return base
    return None


def inspect(digits: str, name: str, block: str) -> dict:
    score, alignment, printable, decoded = printable_pair_score(digits)
    inner = [needle for needle in CONSTANTS if needle in digits and needle != digits]
    witness = composite_witness(int(digits))
    return {
        "block": block, "reading": name, "length": len(digits),
        "digits_sha256": hashlib.sha256(digits.encode()).hexdigest(),
        "printable_pairs": printable, "pair_count": (len(digits) - alignment) // 2,
        "pair_alignment": alignment, "pair_ascii_printable": round(score, 3),
        "pair_ascii_text": decoded, "n_3301": digits.count("3301"),
        "n_1033": digits.count("1033"), "composite_witness": witness,
        "const_match": inner or None,
        "verdict": "HIT(R2)" if score >= .95 else "HIT(R3)" if inner else "null",
    }


def inspect_all(lines: list[str]) -> tuple[list[dict], list[dict]]:
    bare = [inspect(stream, name, "2012_PS") for name, stream in routes(lines).items()]
    indented = [inspect(stream, name, "2012_PS_indent5")
                for name, stream in routes(lines, indent=5).items()]
    return bare, indented


def controls() -> dict:
    planted = 0
    for _ in range(10):
        message = "".join(RNG.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ ") for __ in range(65))
        digits = "".join(f"{ord(character):02d}" for character in message) + str(RNG.randrange(10))
        rows = [digits[i::3] for i in range(3)]
        value = routes(rows)["cols_L2R_top2bot"]
        if printable_pair_score(value)[0] >= .95:
            planted += 1
    negatives_at_80 = 0
    negatives_at_95 = 0
    for _ in range(200):
        random_rows = ["".join(str(RNG.randrange(10)) for __ in range(length))
                       for length in (40, 45, 46)]
        scores = [printable_pair_score(value)[0] for value in routes(random_rows).values()]
        negatives_at_80 += sum(score >= .80 for score in scores)
        negatives_at_95 += sum(score >= .95 for score in scores)
    if planted != 10 or negatives_at_95:
        raise AssertionError("Plant recovery or amended negative control failed")
    return {"planted_recovered": planted, "planted_count": 10,
            "random_blocks": 200, "old_80_percent_gate_firings": negatives_at_80,
            "amended_95_percent_gate_firings": negatives_at_95}


def main() -> None:
    control = controls()
    lines = primary_lines()
    bare, indented = inspect_all(lines)
    report = {"schema": "liberpedia-h03-ps-layout-replay-v1",
              "source_revision": "f08b20b632d91209ddbaa747e8e2f23df0c78ba1",
              "primary_message_sha256": hashlib.sha256((SOURCE / "ky_2012-01-final-message.asc").read_bytes()).hexdigest(),
              "physical_lines": lines, "controls": control,
              "bare_readings": bare, "indented_readings": indented,
              "strict_hits": [row for row in bare + indented if row["verdict"] != "null"]}
    (HERE / "results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"controls": control, "bare": [(r["reading"], r["pair_ascii_printable"], r["n_3301"], r["n_1033"], r["verdict"]) for r in bare],
                      "indented": [(r["reading"], r["pair_ascii_printable"], r["n_3301"], r["n_1033"], r["verdict"]) for r in indented]}, indent=2))


if __name__ == "__main__":
    main()
