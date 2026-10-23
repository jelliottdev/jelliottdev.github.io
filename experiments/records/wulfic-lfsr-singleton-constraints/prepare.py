"""Freeze the three intended manuscript inputs and source-defined singleton positions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
IDS = ("lp2-28", "lp2-24", "lp2-21")
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛂᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
RUNE_TO_IDX = {ch: i for i, ch in enumerate(RUNES)}
RUNE_TO_IDX["ᛄ"] = 11
BREAKS = "-•\n /."


def read_page(page_id: str) -> dict:
    path = ROOT / "data" / "pages" / f"{page_id}.json"
    data = path.read_bytes()
    raw = json.loads(data)["raw"].strip()
    values: list[int] = []
    words: list[tuple[int, int]] = []
    current = 0
    first = 0
    for ch in raw:
        if ch in RUNE_TO_IDX:
            values.append(RUNE_TO_IDX[ch])
            current += 1
        elif ch in BREAKS and current:
            words.append((first, current))
            first += current
            current = 0
    if current:
        words.append((first, current))
    singletons = [start for start, length in words if length == 1]
    assert sum(length for _, length in words) == len(values)
    return {
        "id": page_id,
        "site_page_path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "site_page_sha256": hashlib.sha256(data).hexdigest(),
        "runes": values,
        "singleton_positions": singletons,
        "rune_count": len(values),
        "singleton_count": len(singletons),
    }


def main() -> None:
    pages = [read_page(page_id) for page_id in IDS]
    assert [p["singleton_count"] for p in pages] == [12, 9, 7]
    (HERE / "inputs.json").write_text(json.dumps({"schema": "wulfic-lfsr-inputs-v1", "pages": pages}, indent=2) + "\n", encoding="utf-8")
    lines = [str(len(pages))]
    for p in pages:
        lines.append(f'{p["id"]} {p["rune_count"]} {p["singleton_count"]}')
        lines.append(" ".join(map(str, p["runes"])))
        lines.append(" ".join(map(str, p["singleton_positions"])))
    (HERE / "scan-input.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print([(p["id"], p["rune_count"], p["singleton_count"]) for p in pages])


if __name__ == "__main__":
    main()
