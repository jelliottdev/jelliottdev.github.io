"""Independent byte/input, parsing, candidate, and full-selection check."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
LETTERS = ["F", "U", "TH", "O", "R", "C", "G", "W", "H", "N", "I", "J", "EO", "P", "X", "S", "T", "B", "E", "M", "L", "NG", "OE", "D", "A", "AE", "Y", "IO", "EA"]
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
RUNE_INDEX = {v: i for i, v in enumerate(RUNES)}
REV = {v: i for i, v in enumerate(LETTERS)}
TRIS = {"THE": 100, "AND": 80, "ING": 60, "ION": 50, "ENT": 40, "TIO": 40}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_normal(value):
    return json.loads(json.dumps(value, ensure_ascii=False))


def git_blob(repo: Path, path: str, expected: str) -> bytes:
    data = subprocess.check_output(["git", "-C", str(repo), "show", f"{PLAN['source']['commit']}:{path}"])
    assert sha(data) == expected, path
    return data


def encode_corpus(raw: bytes) -> list[int]:
    s = raw.decode("utf-8", errors="ignore").upper()
    out = []
    i = 0
    while i < len(s):
        found = False
        for width in (3, 2):
            chunk = s[i : i + width]
            if chunk in REV:
                out.append(REV[chunk])
                i += width
                found = True
                break
        if found:
            continue
        ch = s[i]
        if ch == "K":
            ch = "C"
        if ch == "V":
            ch = "U"
        if ch in REV:
            out.append(REV[ch])
        i += 1
    return out


def decode(cipher: list[int], stream: list[int], mode: str) -> list[int]:
    if mode == "beaufort":
        return [(k - c) % 29 for c, k in zip(cipher, stream)]
    assert mode == "sub"
    return [(c - k) % 29 for c, k in zip(cipher, stream)]


def score(plain: list[int]) -> tuple[int, float, str]:
    text = "".join(LETTERS[x] for x in plain)
    score = sum(TRIS.get(text[i : i + 3], 0) for i in range(len(text) - 2))
    counts = Counter(plain)
    n = len(plain)
    ioc = 29 * sum(x * (x - 1) for x in counts.values()) / (n * (n - 1)) if n >= 2 else 0.0
    return score, ioc, text[:200]


def evaluate(cipher: list[int], key: list[int]):
    n = len(cipher)
    repeated = key * (((n + len(key) - 1) // len(key)) + 1)

    def one(offset: int, mode: str):
        plain = decode(cipher, repeated[offset : offset + n], mode)
        value, ioc, head = score(plain)
        return (value, ioc, offset, mode, head)

    coarse = sorted([one(off, mode) for off in range(0, 5001, 100) for mode in ("beaufort", "sub")], reverse=True)
    six = coarse[:6]
    offsets = sorted({o for _, _, off, _, _ in six for o in range(max(0, off - 200), off + 201)})
    all_rows = sorted(coarse + [one(off, mode) for off in offsets for mode in ("beaufort", "sub")], reverse=True)
    return {
        "coarse_top_six": six,
        "refined_offset_count": len(offsets),
        "evaluated_rows": len(all_rows),
        "top_100": all_rows[:100],
        "max_score": all_rows[0][0],
        "all_rows_sha256": sha(json.dumps(all_rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")),
    }


def source_function_oracle(source_bytes: bytes, key: list[int]):
    env = {"__file__": "p25_liberal_offset_sweep.py", "__name__": "pinned_source"}
    exec(compile(source_bytes, "p25_liberal_offset_sweep.py", "exec"), env)
    rng = random.Random(86125)
    for _ in range(40):
        n = rng.randrange(3, 55)
        c = [rng.randrange(29) for _ in range(n)]
        off = rng.randrange(0, 5001)
        mode = rng.choice(["beaufort", "sub"])
        stream = key[off : off + n]
        manual = decode(c, stream, mode)
        literal = env["decrypt_with_key"](c, stream, mode)
        assert manual == literal
        sv, si, st = score(manual)
        source_text = env["indices_to_runeglish"](literal)
        assert sv == env["trigram_score"](source_text)
        assert si == env["compute_ioc"](literal)
        assert st == source_text[:200]


def planted_controls(key: list[int], n: int):
    expected = []
    p = ([2, 18, 24, 9, 23] * ((n + 4) // 5))[:n]
    for offset in (300, 1700, 137):
        for mode in ("beaufort", "sub"):
            segment = key[offset : offset + n]
            c = [(k - x) % 29 if mode == "beaufort" else (x + k) % 29 for x, k in zip(p, segment)]
            assert decode(c, segment, mode) == p
            out = evaluate(c, key)
            match = [r for r in out["top_100"] if r[2] == offset and r[3] == mode]
            if offset in (300, 1700):
                assert match and match[0][0] == score(p)[0]
            expected.append({"offset": offset, "mode": mode, "found_in_top_100": bool(match), "score": match[0][0] if match else None, "best_score": out["max_score"]})
    return expected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-repo", required=True, type=Path)
    args = parser.parse_args()
    actual = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    plan_hash = sha((HERE / "plan.json").read_bytes())
    assert actual["plan_sha256"] == plan_hash
    script = git_blob(args.source_repo, PLAN["source"]["script_path"], PLAN["source"]["script_sha256"])
    page = git_blob(args.source_repo, PLAN["source_inputs"]["source_page_path"], PLAN["source_inputs"]["source_page_sha256"])
    corpus = git_blob(args.source_repo, PLAN["source_inputs"]["corpus_pinned_path"], PLAN["source_inputs"]["corpus_sha256"])
    c = [RUNE_INDEX[ch] for ch in page.decode("utf-8") if ch in RUNE_INDEX]
    k = encode_corpus(corpus)
    assert len(c) == actual["rune_count"] == 255
    assert len(k) == actual["key_rune_count"] == 8187
    source_function_oracle(script, k)
    assert json_normal(planted_controls(k, len(c))) == actual["controls"]
    assert json_normal(evaluate(c, k)) == actual["manuscript"]
    rng = random.Random(20261023)
    expected_nulls = []
    for i in range(199):
        shuffled = c.copy()
        rng.shuffle(shuffled)
        out = evaluate(shuffled, k)
        expected_nulls.append({"trial": i, "cipher_sha256": sha(bytes(shuffled)), "max_score": out["max_score"], "all_rows_sha256": out["all_rows_sha256"], "coarse_top_six": [r[2:4] for r in out["coarse_top_six"]], "evaluated_rows": out["evaluated_rows"]})
    assert json_normal(expected_nulls) == actual["order_control"]["nulls"]
    assert sum(x["max_score"] >= actual["manuscript"]["max_score"] for x in expected_nulls) == actual["order_control"]["at_least_manuscript"]
    print("checked exact source bytes, 40 source function oracles, six plants, page result, and 199 whole-selection controls")


if __name__ == "__main__":
    main()
