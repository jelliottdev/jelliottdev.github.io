"""Check the three saved QuagMirror drafts against source constants and LP2 text."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPECTED = {"OG_quag_mirror.py": 153, "quag_mirror_v4.py": 49,
            "quag_mirror_WIP.py": 500}


def source_constants(path: Path) -> dict:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    wanted = {"section1", "section1_spaces", "latin_fragments", "runes",
              "CC_M", "CP_M", "CA_M", "PC_M", "PP_M", "PA_M", "AC_M", "AP_M", "AA_M"}
    return {node.targets[0].id: ast.literal_eval(node.value)
            for node in tree.body if isinstance(node, ast.Assign)
            and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in wanted}


def manuscript_indices(alphabet: list[str]) -> list[int]:
    values = []
    for number in range(3):
        page = json.loads((ROOT / f"data/pages/lp2-{number:02d}.json").read_text(encoding="utf-8"))
        for rune in page["raw"]:
            # The source calls the J rune ᛂ; Liberpedia's transcription uses ᛄ.
            normalized = "ᛂ" if rune == "ᛄ" else rune
            if normalized in alphabet:
                values.append(alphabet.index(normalized))
    return values


def verify() -> dict:
    saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert saved["source_commit"] == "88ef1e60b0738b8b28db96bc9dc44dc4da8dd307"
    assert {row["source_file"] for row in saved["variants"]} == set(EXPECTED)
    for row in saved["variants"]:
        path = HERE / "source" / row["source_file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["source_sha256"]
        fixed = source_constants(path)
        assert len(fixed["runes"]) == 29 and len(set(fixed["runes"])) == 29
        assert len(fixed["latin_fragments"]) == 29
        assert len(fixed["section1"]) == 729 == row["source_input_length"]
        assert fixed["section1"] == manuscript_indices(fixed["runes"]), "Source input differs from LP2-00–02"
        for name in ("CC_M", "CP_M", "CA_M", "PC_M", "PP_M", "PA_M", "AC_M", "AP_M", "AA_M"):
            assert sorted(fixed[name]) == list(range(29)), f"Invalid mirror table {name}"
        count = row["positions_processed"]
        assert count == EXPECTED[row["source_file"]]
        assert row["ciphertext_indices"] == fixed["section1"][:count]
        assert len(row["autokey_indices"]) == len(row["plaintext_indices"]) == count
        assert all(0 <= value < 29 for value in row["autokey_indices"] + row["plaintext_indices"])
        reconstructed = "".join(
            fixed["latin_fragments"][value] + (" " if i + 1 in fixed["section1_spaces"] else "")
            for i, value in enumerate(row["plaintext_indices"]))
        assert reconstructed == row["final_text"]
    assert saved["variants"][1]["positions_processed"] == 49
    return {"variants": 3, "source_runes_checked": 729,
            "processed_positions": [row["positions_processed"] for row in saved["variants"]],
            "mirror_tables_per_variant": 9, "source_input_matches_lp2_00_to_02": True}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
