"""Bounded forward-lookahead completion of a reported block-feedback idea."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ALPHABET = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᛠᛡᚣ"
INDEX = {r: i for i, r in enumerate(ALPHABET)}
assert len(INDEX) == 29


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encode(plain: list[int], block: int) -> list[int]:
    cipher = []
    for i, value in enumerate(plain):
        if i % block == 0:
            lookahead = plain[i + block] if i + block < len(plain) else 0
            cipher.append((value + lookahead) % 29)
        else:
            cipher.append((value + cipher[-1]) % 29)
    return cipher


def decode(cipher: list[int], block: int) -> list[int]:
    if not cipher:
        return []
    plain = [0] * len(cipher)
    for i in range(1, len(cipher)):
        if i % block:
            plain[i] = (cipher[i] - cipher[i - 1]) % 29
    for i in range(((len(cipher) - 1) // block) * block, -1, -block):
        lookahead = plain[i + block] if i + block < len(cipher) else 0
        plain[i] = (cipher[i] - lookahead) % 29
    return plain


def ioc(stream: list[int]) -> float:
    counts = [stream.count(i) for i in range(29)]
    n = len(stream)
    return sum(c * (c - 1) for c in counts) / (n * (n - 1)) if n > 1 else 0.0


def report() -> dict:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    assert all(sha(ROOT / item["path"]) == item["sha256"] for item in plan["inputs"])
    known = json.loads((ROOT / "data/evidence/known-readings.json").read_text(encoding="utf-8"))
    controls = [(p["page"], p["rune_indices"]) for c in known["controls"] for p in c["decoded_pages"] if p["page"].startswith("lp1-")]
    assert len(controls) == 15
    cribs = [(page, values[:12]) for page, values in controls if len(values) >= 12]
    pages = []
    for number in range(56):
        page = f"lp2-{number:02d}"
        values = [INDEX[c] for c in (ROOT / "text" / f"{page}.txt").read_text(encoding="utf-8") if c in INDEX]
        pages.append((page, values))
    outputs = {}
    for block in plan["block_sizes"]:
        planted = []
        for page, original in controls:
            encrypted = encode(original, block)
            recovered = decode(encrypted, block)
            planted.append({"page": page, "length": len(original), "exact": recovered == original,
                            "encoded_doublets": sum(a == b for a, b in zip(encrypted, encrypted[1:]))})
        decoded = [(page, decode(cipher, block)) for page, cipher in pages]
        for (_, cipher), (_, plain) in zip(pages, decoded):
            assert encode(plain, block) == cipher
        joined = [value for _, stream in decoded for value in stream]
        matches = [{"page": page, "control": control} for page, values in decoded for control, opening in cribs if values[:12] == opening]
        outputs[str(block)] = {
            "positive_controls": planted,
            "decoded": [{"page": page, "length": len(values), "first_24_indices": values[:24],
                         "sha256_indices_csv": hashlib.sha256(",".join(map(str, values)).encode()).hexdigest()} for page, values in decoded],
            "decoded_runes": len(joined), "decoded_ioc": ioc(joined), "decoded_f_count": joined.count(0),
            "known_opening_comparisons": sum(len(values) >= 12 for _, values in decoded) * len(cribs),
            "known_opening_matches": matches,
            "positive_encoded_doublets": sum(x["encoded_doublets"] for x in planted),
            "positive_encoded_edges": sum(x["length"] - 1 for x in planted),
        }
    raw = [value for _, stream in pages for value in stream]
    solved = [value for _, stream in controls for value in stream]
    return {"schema": "liberpedia-block-lookahead-feedback-results-v1", "plan_sha256": sha(HERE / "plan.json"),
            "input_sha256": {item["path"]: item["sha256"] for item in plan["inputs"]},
            "raw_lp2": {"runes": len(raw), "ioc": ioc(raw), "f_count": raw.count(0)},
            "solved_lp1": {"runes": len(solved), "ioc": ioc(solved), "f_count": solved.count(0)},
            "block_cases": outputs}


def main() -> None:
    output = json.dumps(report(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path = HERE / "results.json"
    if "--check" in sys.argv:
        assert path.read_text(encoding="utf-8") == output
        print("Block-lookahead report matches")
    else:
        path.write_text(output, encoding="utf-8", newline="\n")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
