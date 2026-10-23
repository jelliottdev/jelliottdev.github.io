"""Generate nontrivial planted LFSR streams and verify exact parameter recovery."""
from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
POSITIONS = [0, 1, 2, 3, 4, 7, 10, 14, 19, 25]
N = 35


def stream(coeff: list[int], state: list[int]) -> list[int]:
    values = list(state)
    length = len(coeff)
    while len(values) < N:
        values.append(sum(a * b for a, b in zip(coeff, values[-length:])) % 29)
    return values


def controls() -> tuple[list[dict], str]:
    cases = []
    lines = [str(15)]
    for length in range(1, 6):
        coeff = [2] if length == 1 else [1, 1] + [0] * (length - 2)
        state = [3, 5, 7, 9, 11][:length]
        key = stream(coeff, state)
        for mode in ("sub", "add", "beaufort"):
            plain = [18] * N
            for j, pos in enumerate(POSITIONS):
                plain[pos] = 10 if j % 2 == 0 else 24
            if mode == "sub":
                cipher = [(p + k) % 29 for p, k in zip(plain, key)]
                recovered = [(c - k) % 29 for c, k in zip(cipher, key)]
            elif mode == "add":
                cipher = [(p - k) % 29 for p, k in zip(plain, key)]
                recovered = [(c + k) % 29 for c, k in zip(cipher, key)]
            else:
                # Beaufort decrypts K-C, so its ciphertext is K-P.
                cipher = [(k - p) % 29 for p, k in zip(plain, key)]
                recovered = [(k - c) % 29 for c, k in zip(cipher, key)]
            assert recovered == plain
            page_id = f"plant-L{length}-{mode}"
            cases.append({"id": page_id, "length": length, "mode": mode, "coeff": coeff, "state": state})
            lines += [f"{page_id} {N} {len(POSITIONS)}", " ".join(map(str, cipher)), " ".join(map(str, POSITIONS))]
    return cases, "\n".join(lines) + "\n"


def main() -> None:
    cases, text = controls()
    path = HERE / "control-input.txt"
    path.write_text(text, encoding="utf-8")
    exe = HERE / ("scan.exe" if os.name == "nt" else "scan")
    if not exe.exists():
        raise RuntimeError("compile scan.cpp first")
    result = HERE / "control-summary.tsv"
    dump = HERE / "control-candidates.tsv"
    subprocess.run([str(exe), str(path), str(result), "31", str(dump)], check=True)
    rows = list(csv.DictReader(dump.open(encoding="utf-8"), delimiter="\t"))
    found = {(r["page"], int(r["length"]), r["mode"], r["coefficients:state"]) for r in rows}
    for case in cases:
        coeff = ",".join(map(str, case["coeff"]))
        state = ",".join(map(str, case["state"]))
        witness = (case["id"], case["length"], case["mode"], f"{coeff}:{state}")
        if case["mode"] == "add":
            # Scanner enumerates sub and fans out the sign-negated state.
            witness = (case["id"], case["length"], "sub", f"{coeff}:{','.join(str((-v)%29) for v in case['state'])}")
        assert witness in found, witness
    print(f"PASS: {len(cases)} planted exact key/initial-state recoveries")


if __name__ == "__main__":
    main()
