"""Separate E-02v verifier: byte-stream parser and pairwise midranks."""
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = HERE / "source"


def midranks(values):
    return [1 + sum(other < value for other in values)
            + (sum(other == value for other in values) - 1) / 2 for value in values]


def correlation(a, b):
    x, y = midranks(a), midranks(b)
    xbar, ybar = sum(x) / len(x), sum(y) / len(y)
    dot = sum((u - xbar) * (v - ybar) for u, v in zip(x, y))
    norm = math.sqrt(sum((u - xbar) ** 2 for u in x) * sum((v - ybar) ** 2 for v in y))
    return dot / norm if norm else 0.0


def parse(data, mode):
    # Independent chunk parser. A high bit means another base-128 digit follows.
    chunks, chunk = [], []
    for byte in data:
        chunk.append(byte & 127)
        if byte < 128:
            chunks.append(chunk)
            chunk = []
    return [sum(digit * (128 ** (k if mode == "little" else len(parts)-k-1))
                for k, digit in enumerate(parts)) for parts in chunks]


def main():
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    source = json.loads((S / "source-results.json").read_text(encoding="utf-8"))
    assert len(result["rows"]) == 24
    assert result["rows"] == source["E-02v"]
    assert hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest() == result["plan_sha256"]
    ct = (S / "ct.bin").read_bytes()
    starts = [i for i in range(1, len(ct)) if ct[i-1] == ct[i]]
    assert (len(ct), len(starts), starts[0]) == (12956, 86, 122)
    gaps = [starts[i+1] - starts[i] for i in range(85)]
    targets = {"gaps85": gaps, "gaps86_lead122": [122] + gaps}
    for row in result["rows"]:
        data = (S / (row["variant"] + ".bin")).read_bytes()
        if row["encoding"].endswith("_rev"):
            data = data[::-1]
        values = parse(data, "little" if row["encoding"].startswith("leb128") else "big")
        expected = targets[row["target"]]
        n = min(len(values), len(expected))
        assert row["decoded_n"] == len(values) and row["n_used"] == n
        assert row["rho"] == round(correlation(values[:n], expected[:n]), 4)
        assert row["verdict"] == "null" and abs(row["rho"]) < .5
    assert max(abs(r["rho"]) for r in result["rows"]) == result["maximum_absolute_rho"]
    print("PASS independent 24-row parse and tied-rank recount")


if __name__ == "__main__":
    main()
