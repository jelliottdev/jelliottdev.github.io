"""Convert the exhaustive scanner's small summary to checked, readable JSON."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode(cipher: list[int], coeff: list[int], state: list[int], mode: str) -> list[int]:
    key = list(state)
    length = len(coeff)
    while len(key) < len(cipher):
        key.append(sum(a * b for a, b in zip(coeff, key[-length:])) % 29)
    if mode == "sub":
        return [(c - k) % 29 for c, k in zip(cipher, key)]
    if mode == "add":
        return [(c + k) % 29 for c, k in zip(cipher, key)]
    return [(k - c) % 29 for c, k in zip(cipher, key)]


def main() -> None:
    pages = {p["id"]: p for p in json.loads((HERE / "inputs.json").read_text(encoding="utf-8"))["pages"]}
    rows = list(csv.DictReader((HERE / "full-summary.tsv").open(encoding="utf-8"), delimiter="\t"))
    assert len(rows) == 45
    result_rows = []
    for row in rows:
        page = pages[row["page"]]
        length = int(row["length"])
        mode = row["mode"]
        out = {
            "page": row["page"], "length": length, "mode": mode,
            "polynomials": int(row["polynomials"]),
            "first_basis_invertible": int(row["invertible"]),
            "best_singletons_matched": int(row["best"]),
            "full_singleton_matches": int(row["full"]),
            "examples": [],
        }
        assert out["polynomials"] == 29 ** length
        assert out["best_singletons_matched"] <= page["singleton_count"]
        for item in filter(None, row["samples"].split(";")):
            a, b = item.split(":")
            coeff = list(map(int, a.split(",")))
            state = list(map(int, b.split(",")))
            assert len(coeff) == len(state) == length
            plain = decode(page["runes"], coeff, state, mode)
            singleton_values = [plain[i] for i in page["singleton_positions"]]
            assert set(singleton_values) <= {10, 24}
            freq = Counter(plain)
            n = len(plain)
            normalized_ioc = 29 * sum(v * (v - 1) for v in freq.values()) / (n * (n - 1))
            out["examples"].append({
                "coefficients": coeff, "initial_state": state,
                "full_page_decode_sha256": hashlib.sha256(bytes(plain)).hexdigest(),
                "singleton_values": singleton_values,
                "normalized_ioc": round(normalized_ioc, 6),
            })
        assert len(out["examples"]) == min(5, out["full_singleton_matches"])
        result_rows.append(out)
    result = {
        "schema": "wulfic-lfsr-singleton-results-v1",
        "plan_sha256": sha(HERE / "plan.json"),
        "source_cpp_sha256": sha(HERE / "scan.cpp"),
        "inputs_sha256": sha(HERE / "inputs.json"),
        "full_scan_tsv_sha256": sha(HERE / "full-summary.tsv"),
        "control_input_sha256": sha(HERE / "control-input.txt"),
        "control_candidate_sha256": sha(HERE / "control-candidates.tsv"),
        "controls": "15 planted exact coefficient/initial-state recoveries; three modes at each L=1..5",
        "rows": result_rows,
    }
    (HERE / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print([(p, l, m, r["full_singleton_matches"]) for r in result_rows for p,l,m in [(r["page"],r["length"],r["mode"])] if m=="sub"])


if __name__ == "__main__":
    main()
