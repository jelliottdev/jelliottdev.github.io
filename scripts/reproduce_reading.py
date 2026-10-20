"""Reproduce published Liber Primus readings. Python 3; standard library only.

Run from any directory:
  python scripts/reproduce_reading.py --list
  python scripts/reproduce_reading.py warning
  python scripts/reproduce_reading.py welcome --trace
  python scripts/reproduce_reading.py --check-all

This reproduces known controls; it is not an automatic solver for unsolved pages.
"""
from pathlib import Path
import argparse
import csv
import io
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
LATIN = "F U TH O R C G W H N I J EO P X S T B E M L NG OE D A AE Y IA EA".split()
INDEX = {r: i for i, r in enumerate(RUNES)}


def prime_stream():
    found = []
    candidate = 2
    while True:
        if all(candidate % p for p in found if p*p <= candidate):
            found.append(candidate)
            yield candidate
        candidate += 1


def reproduce(control):
    results, trace = {}, []
    global_ordinal = 0
    key_position = control["start"]
    primes = prime_stream()
    for _ in range(control["start"]):
        next(primes)
    for page_id in control["pages"]:
        text = (ROOT / f"text/{page_id}.txt").read_text(encoding="utf-8")
        # This specific documented source correction is required for the control.
        # It is not a general operation on unsolved ciphertext.
        if page_id == "lp1-10":
            chars = list(text)
            positions = [i for i, ch in enumerate(chars) if ch in INDEX]
            a, b = positions[116], positions[117]
            chars[a], chars[b] = chars[b], chars[a]
            text = "".join(chars)
        if control["boundary"] == "reset":
            global_ordinal = 0
            key_position = control["start"]
            primes = prime_stream()
            for _ in range(control["start"]):
                next(primes)
        out = []
        local_ordinal = 0
        for char in text:
            if char not in INDEX:
                out.append(char)
                continue
            value = INDEX[char]
            skipped = global_ordinal in control["skip"]
            amount = None
            method = control["method"]
            key_before = key_position if method in ("vigenere", "prime-minus-one") else ""
            key_slot = key_position % len(control["key"]) if method == "vigenere" else ""
            if skipped or method == "direct":
                decoded = value
            elif method == "atbash":
                decoded = 28-value
            elif method == "shifted-atbash":
                decoded = (28-value+control["shift"]) % 29
            elif method in ("vigenere", "prime-minus-one"):
                amount = (control["key"][key_position % len(control["key"])]
                          if method == "vigenere" else next(primes)-1)
                decoded = (value-amount) % 29
                key_position += 1
            else:
                raise ValueError(f"Unsupported documented method: {method}")
            out.append(LATIN[decoded])
            trace.append([page_id, local_ordinal, global_ordinal, char, value,
                          "" if amount is None else amount, decoded, LATIN[decoded], skipped, key_before,
                          key_position if key_before != "" else "", key_slot])
            local_ordinal += 1
            global_ordinal += 1
        results[page_id] = "".join(out)
    return results, trace


def check(results):
    for page_id, actual in results.items():
        expected = json.loads((ROOT / f"data/pages/{page_id}.json").read_text(encoding="utf-8"))
        if actual != expected["reading"]["literal"]:
            raise ValueError(f"{page_id}: output differs from the published literal reading")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("section", nargs="?")
    parser.add_argument("--list", action="store_true", help="List the nine known controls")
    parser.add_argument("--trace", action="store_true", help="Write a per-rune CSV trace to stdout")
    parser.add_argument("--check-all", action="store_true", help="Compare all 17 runic page outputs exactly")
    parser.add_argument("--output", type=Path,
                        help="Save a section reading or trace as UTF-8; refuse existing files")
    args = parser.parse_args()
    if args.output and (args.list or args.check_all):
        parser.error("--output requires a section reading or --trace, not --list or --check-all.")
    controls = json.loads((ROOT / "data/evidence/reading-methods.json").read_text(encoding="utf-8"))["controls"]
    if args.list:
        for row in controls:
            print(f'{row["id"]:20} {row["method"]:16} {", ".join(row["pages"])}')
        return
    if args.check_all:
        total = 0
        for row in controls:
            output, _ = reproduce(row)
            check(output)
            total += len(output)
        print(f"PASS: {total} literal page readings match the published controls exactly.")
        return
    row = next((r for r in controls if r["id"] == args.section), None)
    if not row:
        parser.error("Choose a section from --list, or use --check-all.")
    output, trace = reproduce(row)
    check(output)
    rendered = io.StringIO(newline="")
    if args.trace:
        writer = csv.writer(rendered, lineterminator="\n")
        writer.writerow(["page", "page_rune_ordinal", "section_rune_ordinal", "input_rune",
                         "input_index", "subtracted_value", "output_index", "latin", "copied",
                         "key_position_before", "key_position_after", "key_slot_before"])
        writer.writerows(trace)
    else:
        for page_id, text in output.items():
            print(f"=== {page_id.upper()} ===\n{text}", file=rendered)
    if args.output:
        try:
            with args.output.open("x", encoding="utf-8", newline="") as destination:
                destination.write(rendered.getvalue())
        except FileExistsError:
            parser.error(f"Output already exists: {args.output}. Choose a new filename.")
        except OSError as error:
            parser.error(f"Could not save output: {error}")
        print(f"Saved UTF-8 {'CSV trace' if args.trace else 'reading'}: {args.output}")
    else:
        sys.stdout.write(rendered.getvalue())


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", newline="")
    main()
