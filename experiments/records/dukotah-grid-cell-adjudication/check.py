"""Independent receipt comparison and base-60 arithmetic audit for A-04."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ALPHA = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx"
CONTESTED = (25, 175, 182, 199, 215, 237)


def same(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) < 1e-10
    return a == b


def main():
    out = HERE / "replay-output"
    for name in ("grid.json", "calibration.json", "glyphmatch.json", "pixelmatch.json", "adjudication.json"):
        expected = json.loads((HERE / name).read_text(encoding="utf-8"))
        actual = json.loads((out / name).read_text(encoding="utf-8"))
        assert same(expected, actual), f"source output mismatch: {name}"
    grid = json.loads((out / "grid.json").read_text(encoding="utf-8"))
    assert [len(grid[p]) for p in ("p49", "p50", "p51")] == [80, 104, 72]
    cal = json.loads((out / "calibration.json").read_text(encoding="utf-8"))
    assert cal["overall_correct"] == 40 and cal["overall_n"] == 40
    assert len(set(cal["sample"])) == 40
    px = json.loads((out / "pixelmatch.json").read_text(encoding="utf-8"))
    adj = json.loads((out / "adjudication.json").read_text(encoding="utf-8"))
    canon = (HERE / "source/liber-primus/analysis/pp49_51/canon_256.bin").read_bytes()
    decimal = (HERE / "source/liber-primus/analysis/pp49_51/canon_256_decpref.bin").read_bytes()
    assert len(canon) == len(decimal) == 256
    for i in CONTESTED:
        row = adj[str(i)]
        token = row["token"]
        value = 60 * ALPHA.index(token[0]) + ALPHA.index(token[1])
        assert value == row["byte"] == canon[i], (i, token, value)
        assert value != decimal[i], i
        assert row["visual_passes"] == [token] * 3
        assert px["contested"][str(i)]["token"] == token
    print("A-04: five source outputs match; 256 grid cells, 40/40 saved reads, six token/byte checks PASS")


if __name__ == "__main__":
    main()
