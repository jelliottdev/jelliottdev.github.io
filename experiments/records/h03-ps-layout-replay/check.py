#!/usr/bin/env python3
"""Independent source-byte, route and result check; no imports from the replay."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def ensure(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError(reason)


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def get_lines() -> list[str]:
    text = (HERE / "source/ky_2012-01-final-message.asc").read_text(encoding="utf-8")
    signed = text.partition("-----BEGIN PGP SIGNATURE-----")[0]
    found = re.search(r"^P\.S\. ([0-9]+)\\\s*\n([0-9]+)\\\s*\n([0-9]+)\s*$",
                      signed, flags=re.MULTILINE)
    ensure(found is not None, "No exact three-line P.S. block")
    lines = list(found.groups())
    ensure([len(x) for x in lines] == [40, 45, 46], "Physical line geometry differs")
    return lines


def route_strings(lines: list[str], indent: bool) -> dict[str, str]:
    # Build coordinate triples, then order them in each direction. This is
    # intentionally unlike the runner's column/row nested loops.
    symbols = [(r, c + (5 if indent and r == 0 else 0), digit)
               for r, row in enumerate(lines) for c, digit in enumerate(row)]
    output = {}
    for c_reverse, r_reverse, name in (
        (False, False, "cols_L2R_top2bot"), (False, True, "cols_L2R_bot2top"),
        (True, False, "cols_R2L_top2bot"), (True, True, "cols_R2L_bot2top"),
    ):
        ordered = sorted(symbols, key=lambda item: ((-item[1] if c_reverse else item[1]),
                                                    (-item[0] if r_reverse else item[0])))
        output[name] = "".join(item[2] for item in ordered)
    if not indent:
        flat = "".join(lines)
        output.update({"concat_fwd": flat, "concat_rev": flat[::-1]})
    return output


def best_fraction(stream: str) -> tuple[int, int, int]:
    candidates = []
    for align in (0, 1):
        codes = [10 * (ord(stream[k]) - 48) + (ord(stream[k + 1]) - 48)
                 for k in range(align, len(stream) - 1, 2)]
        candidates.append((sum(32 <= number <= 126 for number in codes), len(codes), align))
    return max(candidates, key=lambda item: (item[0] / item[1], -item[2]))


def prove_composite(number: int, witness: int) -> bool:
    if number % witness == 0:
        return True
    d = number - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    value = pow(witness, d, number)
    if value in (1, number - 1):
        return False
    for _ in range(s - 1):
        value = value * value % number
        if value == number - 1:
            return False
    return True


def main() -> None:
    manifest = json.loads((HERE / "source-manifest.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        ensure(git_blob_sha((HERE / item["local"]).read_bytes()) == item["git_blob_sha1"],
               "Pinned source bytes changed: " + item["local"])
    report = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    source = json.loads((HERE / "source/results.json").read_text(encoding="utf-8"))
    lines = get_lines()
    ensure(lines == report["physical_lines"] == source["H-03r"]["lines"],
           "Source digit lines differ")
    ensure(report["source_revision"] == manifest["revision"], "Pinned revision mismatch")
    ensure(report["primary_message_sha256"] ==
           hashlib.sha256((HERE / "source/ky_2012-01-final-message.asc").read_bytes()).hexdigest(),
           "Source text digest mismatch")
    for indented, current, original in (
        (False, report["bare_readings"], source["H-03r"]["rows"]),
        (True, report["indented_readings"], source["H-03r_indent5"]),
    ):
        route_map = route_strings(lines, indented)
        ensure(len(current) == len(original) == len(route_map) == (4 if indented else 6),
               "Unexpected route count")
        by_name = {item["reading"]: item for item in current}
        source_by_name = {item["reading"]: item for item in original}
        ensure(set(by_name) == set(source_by_name) == set(route_map), "Route names differ")
        for name, stream in route_map.items():
            row, historic = by_name[name], source_by_name[name]
            count, length, alignment = best_fraction(stream)
            score = round(count / length, 3)
            ensure(row["length"] == historic["len"] == len(stream) == 131,
                   name + ": length")
            ensure(row["digits_sha256"] == hashlib.sha256(stream.encode()).hexdigest(),
                   name + ": stream digest")
            ensure((row["printable_pairs"], row["pair_count"], row["pair_alignment"],
                    row["pair_ascii_printable"]) == (count, length, alignment, score),
                   name + ": printable pairs")
            ensure(historic["pair_ascii_printable"] == score, name + ": source score")
            ensure(row["n_3301"] == historic["n_3301"] == stream.count("3301") and
                   row["n_1033"] == historic["n_1033"] == stream.count("1033"),
                   name + ": motif count")
            ensure(row["composite_witness"] is not None and
                   prove_composite(int(stream), row["composite_witness"]) and
                   historic["is_prime"] is False, name + ": composite proof")
            ensure(row["verdict"] == historic["verdict"] == "null", name + ": verdict")
    controls = report["controls"]
    ensure(controls["planted_recovered"] == controls["planted_count"] == 10,
           "Planted-column recovery")
    ensure(controls["random_blocks"] == 200 and
           controls["amended_95_percent_gate_firings"] == 0 and
           controls["old_80_percent_gate_firings"] > 0,
           "Gate calibration")
    ensure(source["controls"]["H-03r"] == {"recovery": 1.0, "neg_hits_200": 0},
           "Pinned source controls")
    ensure(report["strict_hits"] == [], "A strict hit was omitted")
    print("PASS: exact pinned 2012 P.S. bytes, all 10 layouts, matching source rows, "
          "10 planted controls and 200 random blocks")


if __name__ == "__main__":
    main()
