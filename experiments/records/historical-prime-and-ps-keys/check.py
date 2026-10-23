"""Independent case accounting for the pinned Campaign VII B3 source replay."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source/liber-primus"
ORIGINAL = SOURCE / "analysis/campaign7/original_results.json"
CASES = HERE / "cases.jsonl"
RESULTS = HERE / "results.json"
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
TRANS = ("F", "U", "TH", "O", "R", "C", "G", "W", "H", "N", "I", "J", "EO",
         "P", "X", "S", "T", "B", "E", "M", "L", "NG", "OE", "D", "A", "AE", "Y", "IA", "EA")
RUNE_INDEX = {r: i for i, r in enumerate(RUNES)}
PS = ("1041279065891998535982789873959431895640"
      "442510695567564373922695237268242385295908173"
      "9834390370374475764863415203423499357108713631")
ALPHA = re.compile("[^A-Z]")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def primes_between(lo: int, hi: int) -> list[int]:
    return [n for n in range(lo, hi + 1)
            if n >= 2 and all(n % d for d in range(2, math.isqrt(n) + 1))]


def streams() -> dict[str, list[int]]:
    missing = primes_between(73, 1223)
    value = int(PS)
    base29 = []
    while value:
        value, rem = divmod(value, 29)
        base29.append(rem)
    return {
        "ps_digits": [int(c) for c in PS],
        "ps_2dig": [int(PS[i:i + 2]) % 29 for i in range(0, len(PS) - 1, 2)],
        "ps_base29": base29[::-1],
        "missing_primes": [p % 29 for p in missing],
        "missing_gaps": [(b - a) % 29 for a, b in zip(missing, missing[1:])],
        "trail_2012": [0, 2, 3, 5, 7, 11, 13, 1, 1, 2, 11, 0, 7, 0, 5, 0, 3, 2],
        "trail_2013": [5, 3, 2, 2, 3, 5],
        "trail_2014": [2, 3, 5, 7, 11, 13, 17, 23, 0, 2, 8],
        "trail_2015": [5, 3, 2, 5, 7],
    }


def score_table() -> tuple[dict[str, float], float]:
    counts = {}
    for row in (SOURCE / "data/english_quadgrams.txt").read_text(encoding="ascii").splitlines():
        gram, count = row.split()
        counts[gram] = int(count)
    total = sum(counts.values())
    return ({gram: math.log10(count / total) for gram, count in counts.items()},
            math.log10(0.01 / total))


def score(text: str, table: dict[str, float], floor: float) -> float:
    letters = ALPHA.sub("", text.upper())
    if len(letters) < 4:
        return -999.0
    return sum(table.get(letters[i:i + 4], floor) for i in range(len(letters) - 3)) / (len(letters) - 3)


def decode(cipher: list[int], key: list[int], sign: int, atbash: bool, interrupt: bool) -> str:
    out = []
    slot = 0
    for symbol in cipher:
        if interrupt and symbol == 0:
            out.append("F")
            continue
        transformed = 28 - symbol if atbash else symbol
        out.append(TRANS[(transformed + sign * key[slot % len(key)]) % 29])
        slot += 1
    return "".join(out)


def encode(plain: list[int], key: list[int], sign: int, atbash: bool, interrupt: bool) -> list[int]:
    """Inverse of the exact setting; used solely for an out-of-corpus power check."""
    cipher = []
    slot = 0
    for symbol in plain:
        if interrupt and symbol == 0:
            cipher.append(0)
            continue
        shifted = (symbol - sign * key[slot % len(key)]) % 29
        cipher.append(28 - shifted if atbash else shifted)
        slot += 1
    return cipher


def planted_controls(keys: dict[str, list[int]], table: dict[str, float], floor: float) -> list[dict]:
    sample = "WELCOME PILGRIM TO THE GREAT JOURNEY WELCOME PILGRIM TO THE GREAT JOURNEY"
    aliases = {"V": "U", "K": "C", "Z": "S", "Q": "C"}
    normalized = "".join(aliases.get(c, c) for c in sample.upper() if c.isalpha())
    # Longest-first only for tokens occurring in this specific fixed control text.
    units = sorted(((t, i) for i, t in enumerate(TRANS)), key=lambda pair: -len(pair[0]))
    plain = []
    while normalized:
        token, index = next((token, index) for token, index in units if normalized.startswith(token))
        plain.append(index)
        normalized = normalized[len(token):]
    expected = "".join(TRANS[i] for i in plain)
    assert len(plain) == 58 and score(expected, table, floor) > -5.2
    controls = []
    sys.path.insert(0, str(SOURCE / "src"))
    from lp import ciphers as source_ciphers, gematria as source_gp
    for name, sign, atbash, interrupt in (("missing_primes", -1, False, False),
                                           ("missing_primes", 1, True, True)):
        fixture = plain[:20] + [0] + plain[20:] if interrupt else plain
        expected = "".join(TRANS[i] for i in fixture)
        cipher = encode(fixture, keys[name], sign, atbash, interrupt)
        recovered = decode(cipher, keys[name], sign, atbash, interrupt)
        assert recovered == expected
        source_runes = "".join(RUNES[i] for i in cipher)
        source_recovered, _ = source_ciphers.transform_runes(
            source_runes, lambda length, k=keys[name]: source_ciphers.repeat_key(k, length),
            sign=sign, interrupters=interrupt, atbash=atbash)
        assert source_recovered == expected and source_gp.runes_to_indices(source_runes) == cipher
        if interrupt:
            assert cipher.count(0) == 1  # the planted F is copied without key advance
        controls.append({"key": name, "sign": sign, "atbash": atbash,
                         "interrupter": interrupt, "runes": len(fixture),
                         "recovered": True, "score": round(score(recovered, table, floor), 6)})
    return controls


def analyze() -> tuple[list[dict], dict]:
    source = (SOURCE / "data/krisyotam_runes.txt").read_text(encoding="utf-8")
    pages = [[RUNE_INDEX[c] for c in segment if c in RUNE_INDEX]
             for segment in source.split("%")]
    pages = [page for page in pages if page]
    assert len(pages) == 57 and sum(map(len, pages[:-2])) == 12956
    targets = {f"p{i:02d}": page for i, page in enumerate(pages[:-2])}
    targets["WHOLE"] = [symbol for page in pages[:-2] for symbol in page]
    keys = streams()
    missing = primes_between(73, 1223)
    assert len(missing) == 180 and missing[:3] == [73, 79, 83] and missing[-3:] == [1213, 1217, 1223]
    assert len(PS) == 131
    table, floor = score_table()
    cases = []
    best = {}
    winner = None
    for name, key in keys.items():
        for target, cipher in targets.items():
            for sign in (-1, 1):
                for atbash in (False, True):
                    for interrupt in (False, True):
                        plaintext = decode(cipher, key, sign, atbash, interrupt)
                        value = score(plaintext, table, floor)
                        case = {"stream": name, "target": target, "sign": sign,
                                "atbash": atbash, "interrupter": interrupt,
                                "score": round(value, 6), "plaintext_prefix": plaintext[:80]}
                        cases.append(case)
                        if value > best.get(name, -99):
                            best[name] = value
                        if winner is None or value > winner[0]:
                            winner = (value, case)
    original = json.loads(ORIGINAL.read_text(encoding="utf-8"))
    assert len(cases) == 4032 and original["n_hits"] == 0
    assert round(winner[0], 3) == original["best_score"]
    assert all(round(best[name], 3) == original["per_stream_best"][name] for name in keys)
    assert winner[1]["stream"] == original["best"]["stream"]
    assert winner[1]["target"] == original["best"]["target"]
    assert winner[1]["plaintext_prefix"] == original["best"]["plaintext"]
    assert all(row["score"] <= -5.2 for row in cases)
    report = {
        "source_revision": "f08b20b632d91209ddbaa747e8e2f23df0c78ba1",
        "source_program_sha256": digest((SOURCE / "analysis/campaign7/b3_hints.py").read_bytes()),
        "corpus_sha256": digest((SOURCE / "data/krisyotam_runes.txt").read_bytes()),
        "quadgrams_sha256": digest((SOURCE / "data/english_quadgrams.txt").read_bytes()),
        "source_community_note_sha256": digest((HERE / "source/community/krisyotam_HINTS-NEVER-USED.md").read_bytes()),
        "missing_prime_count": len(missing), "missing_prime_first_last": [missing[0], missing[-1]],
        "stream_lengths": {name: len(key) for name, key in keys.items()},
        "source_targets": len(targets), "target_runes": sum(map(len, pages[:-2])),
        "case_count": len(cases), "threshold": -5.2,
        "best": winner[1], "per_stream_best": {name: round(value, 3) for name, value in best.items()},
        "passing_cases": 0,
        "planted_controls": planted_controls(keys, table, floor),
        "source_result_match": True,
    }
    return cases, report


def main() -> None:
    cases, report = analyze()
    lines = "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in cases)
    if "--write" in sys.argv:
        CASES.write_text(lines, encoding="utf-8", newline="\n")
        report["cases_sha256"] = digest(lines.encode("utf-8"))
        RESULTS.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8", newline="\n")
    else:
        saved = json.loads(RESULTS.read_text(encoding="utf-8"))
        report["cases_sha256"] = digest(lines.encode("utf-8"))
        assert saved == report and CASES.read_bytes() == lines.encode("utf-8")
    print(json.dumps({"cases": report["case_count"], "best": report["best"],
                      "planted_controls": report["planted_controls"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
