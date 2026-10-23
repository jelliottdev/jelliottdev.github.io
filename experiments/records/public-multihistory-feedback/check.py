"""Check source identity, whole-grid count and the winning decode independently."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "source/analysis/round12/C1/results.json"
OLD = HERE / "source/analysis/round12/C1/original_results.json"
TEXT = HERE / "source/data/krisyotam_runes.txt"
QGRAM = HERE / "source/data/english_quadgrams.txt"
CONTROL = HERE / "controls.json"
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
TRANS = ("F", "U", "TH", "O", "R", "C", "G", "W", "H", "N", "I", "J", "EO", "P", "X", "S", "T", "B", "E", "M", "L", "NG", "OE", "D", "A", "AE", "Y", "IA", "EA")


def quadgram_score(text: str) -> float:
    counts = {}
    for line in QGRAM.read_text(encoding="ascii").splitlines():
        gram, count = line.split()
        counts[gram] = int(count)
    total = sum(counts.values())
    floor = math.log10(0.01) - math.log10(total)
    scored = [math.log10(counts[g]) - math.log10(total) if g in counts else floor
              for g in (text[i:i+4] for i in range(len(text)-3))]
    return sum(scored) / len(scored)


def verify() -> dict:
    result = json.loads(OUT.read_text(encoding="utf-8"))
    original = json.loads(OLD.read_text(encoding="utf-8"))
    control = json.loads(CONTROL.read_text(encoding="utf-8"))
    assert {k: control[k] for k in ("source_controls", "history_sources", "functions", "k", "all_passed")} == {
        "source_controls": 21, "history_sources": 3,
        "functions": 7, "k": 3, "all_passed": True}
    assert -4.2 < control["english_score"] < -4.1
    lookup = {r: i for i, r in enumerate(RUNES)}
    assert len(lookup) == 29
    sections = TEXT.read_text(encoding="utf-8").split("%")
    streams = [[lookup[r] for r in s if r in lookup] for s in sections[:55]]
    assert len(streams) == 55 and sum(map(len, streams)) == 12956
    assert all(len(s) >= 12 for s in streams)
    assert result["n_configs"] == (len(streams) + 1) * 7 * 5 * 3 * 2 * 2 == 23520
    assert result["hit_bar"] == -5.5
    assert result["top20"] == original["top20"]
    assert abs(result["null_max"] - original["null_max"]) < 0.0001
    assert all(x["score"] < result["hit_bar"] for x in result["top20"])

    # Separate implementation of the strongest reported rule: reversed seg49,
    # five-symbol plaintext XOR history, all-equal seed six, negative sign.
    top = result["top20"][0]
    assert {k: top[k] for k in ("label", "orient", "sign", "f", "k", "source", "seed")} == {
        "label": "seg49", "orient": "rev", "sign": -1, "f": "xor", "k": 5,
        "source": "pt", "seed": "eq6"}
    ciphertext = list(reversed(streams[49]))
    plain = []
    for i, c in enumerate(ciphertext):
        key = 6 if i < 5 else 0
        if i >= 5:
            for value in plain[-5:]:
                key ^= value
        plain.append((c - key % 29) % 29)
    translit = "".join(TRANS[i] for i in plain[5:])
    assert top["translit"] == "".join(TRANS[i] for i in plain[5:65])
    assert round(quadgram_score(translit), 4) == top["score"]
    return {"runes": sum(map(len, streams)), "segments": len(streams),
            "configs": result["n_configs"], "best_score": top["score"],
            "bar": result["hit_bar"],
            "transcription_sha256": hashlib.sha256(TEXT.read_bytes()).hexdigest()}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
