"""Independent block-equation oracle for the fixed lookahead decoder."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
REPORT = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᛠᛡᚣ"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def block_oracle(cipher, size):
    """Solve all block-start pair sums backward, then internal differences."""
    blocks = [cipher[start:start + size] for start in range(0, len(cipher), size)]
    firsts = [0] * len(blocks)
    following = 0
    for b in range(len(blocks) - 1, -1, -1):
        firsts[b] = (blocks[b][0] - following) % 29
        following = firsts[b]
    answer = []
    for first, block in zip(firsts, blocks):
        answer.append(first)
        answer.extend((right - left) % 29 for left, right in zip(block, block[1:]))
    return answer


def check():
    assert digest(HERE / "plan.json") == REPORT["plan_sha256"]
    assert len(PLAN["inputs"]) == 57
    for item in PLAN["inputs"]:
        assert digest(ROOT / item["path"]) == item["sha256"] == REPORT["input_sha256"][item["path"]]
    known = json.loads((ROOT / "data/evidence/known-readings.json").read_text(encoding="utf-8"))
    controls = [p["rune_indices"] for c in known["controls"] for p in c["decoded_pages"] if p["page"].startswith("lp1-")]
    assert len(controls) == 15
    pages = []
    for i in range(56):
        text = (ROOT / "text" / f"lp2-{i:02d}.txt").read_text(encoding="utf-8")
        pages.append([RUNES.index(c) for c in text if c in RUNES])
    for size in PLAN["block_sizes"]:
        case = REPORT["block_cases"][str(size)]
        assert all(entry["exact"] for entry in case["positive_controls"])
        for original in controls:
            encrypted = []
            for start in range(0, len(original), size):
                block = original[start:start + size]
                next_first = original[start + size] if start + size < len(original) else 0
                enc = [(block[0] + next_first) % 29]
                for rune in block[1:]:
                    enc.append((rune + enc[-1]) % 29)
                encrypted.extend(enc)
            assert block_oracle(encrypted, size) == original
        decoded = [block_oracle(page, size) for page in pages]
        rows = case["decoded"]
        assert len(rows) == len(decoded)
        for number, (values, row) in enumerate(zip(decoded, rows)):
            assert row["page"] == f"lp2-{number:02d}"
            assert row["length"] == len(values)
            assert row["first_24_indices"] == values[:24]
            assert row["sha256_indices_csv"] == hashlib.sha256(",".join(map(str, values)).encode()).hexdigest()
        flat = [v for page in decoded for v in page]
        counts = [flat.count(i) for i in range(29)]
        assert case["decoded_runes"] == len(flat)
        assert case["decoded_f_count"] == counts[0]
        assert abs(case["decoded_ioc"] - sum(x * (x - 1) for x in counts) / (len(flat) * (len(flat) - 1))) < 1e-15
        matching = sum(values[:12] == original[:12] for values in decoded if len(values) >= 12 for original in controls)
        assert matching == len(case["known_opening_matches"]) == 0
        assert case["known_opening_comparisons"] == 825
    print("Independent block-equation oracle verifies inputs, all outputs and planted controls")


if __name__ == "__main__":
    check()
