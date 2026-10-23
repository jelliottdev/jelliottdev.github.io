"""Independent structural and numerical checks of the Round 16 source replay."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "source" / "analysis" / "round16" / "prng" / "results.json"
ORIGINAL = HERE / "source" / "analysis" / "round16" / "prng" / "original_results.json"
TEXT = HERE / "source" / "data" / "krisyotam_runes.txt"
CT = HERE / "source" / "analysis" / "seed_sweep" / "ct.bin"
ALPHABET = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"


def verify(output: Path = OUT) -> dict:
    run = json.loads(output.read_text(encoding="utf-8"))
    historic = json.loads(ORIGINAL.read_text(encoding="utf-8"))
    rune_index = {r: n for n, r in enumerate(ALPHABET)}
    assert len(rune_index) == 29
    sections = TEXT.read_text(encoding="utf-8").split("%")
    expected_ct = bytes(rune_index[r] for s in sections[:55] for r in s if r in rune_index)
    assert expected_ct == CT.read_bytes(), "Ciphertext is not the pinned source's first 55 sections"
    assert len(expected_ct) == 12956 and expected_ct.count(0) == 458

    assert run["positive_control"] is True
    assert run["ctrl_match"] >= 0.90
    assert run["ctrl_score"] >= run["effective_bar"]
    assert len(run["generators_swept"]) == 7
    assert run["seeds_count"] == 1877
    assert run["total_decodes"] == 7 * 1877 * 2 * 2
    assert run["best_config"]["score"] == run["best_score"]
    assert max(row["score"] for row in run["top20"]) == run["best_score"]
    assert all(row["score"] < run["effective_bar"] for row in run["top20"])
    assert run["verdict"] == "NEGATIVE"

    # The archived run is an independent execution of the same source script.
    # Small platform-dependent floating differences are allowed; a different
    # winning generator, seed, sign, or direction is not.
    for key in ("gen", "seed", "sign", "dir"):
        assert run["best_config"][key] == historic["best_config"][key]
    assert abs(run["best_score"] - historic["best_score"]) < 0.005
    assert abs(run["null_max"] - historic["null_max"]) < 0.005

    # Self-generated reference vectors are not independent validation of PHP,
    # .NET or ISAAC implementations. Keep that limitation explicit in the article.
    assert all(run["validation_results"][name]["self_consistent"] for name in run["generators_swept"])
    return {
        "ciphertext_sha256": hashlib.sha256(expected_ct).hexdigest(),
        "source_revision": "f08b20b632d91209ddbaa747e8e2f23df0c78ba1",
        "seed_count": run["seeds_count"],
        "decode_count": run["total_decodes"],
        "best_score": run["best_score"],
        "bar": run["effective_bar"],
        "control_score": run["ctrl_score"],
        "historical_best_delta": run["best_score"] - historic["best_score"],
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
