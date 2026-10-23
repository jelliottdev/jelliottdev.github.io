"""Independent payload/gap rank check using pairwise midranks."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def midranks(seq):
    return [(1 + sum(other < value for other in seq)
             + sum(other <= value for other in seq)) / 2 for value in seq]


def corr(a, b):
    n = min(len(a), len(b))
    x, y = midranks(a[:n]), midranks(b[:n])
    xbar = sum(x)/n
    ybar = sum(y)/n
    numerator = sum((p-xbar)*(q-ybar) for p, q in zip(x, y))
    denominator = (sum((p-xbar)**2 for p in x)*sum((q-ybar)**2 for q in y))**0.5
    return numerator/denominator


def read_varint(data, reverse_order, high_first):
    if reverse_order:
        data = data[::-1]
    output = []
    pending = []
    for byte in data:
        pending.append(byte)
        if byte & 128:
            continue
        if high_first:
            number = 0
            for component in pending:
                number = 128*number + (component & 127)
        else:
            number = sum((component & 127)*128**i for i, component in enumerate(pending))
        output.append(number)
        pending = []
    return output


payload = (ROOT / "experiments/records/grid-page-order-permutations/source/canon_256.bin").read_bytes()
positions = [e["global_rune_index_zero_based"] for e in json.loads(
    (ROOT / "experiments/records/doublet-placement/results.json").read_text(encoding="utf-8"))["event_slots"]]
gaps = [positions[i+1]-positions[i] for i in range(len(positions)-1)]
inputs = {
    "uint8": list(payload),
    "uint16_le": [payload[i] + 256*payload[i+1] for i in range(0, 256, 2)],
    "uint16_be": [256*payload[i] + payload[i+1] for i in range(0, 256, 2)],
}
for family, high_first in (("leb128", False), ("msb128", True)):
    for direction, backwards in (("forward", False), ("reverse", True)):
        inputs[f"{family}_{direction}"] = read_varint(payload, backwards, high_first)
result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
for row in result["readings"]:
    target = gaps if row["target"] == "gaps85" else [positions[0]+1] + gaps
    candidate = inputs[row["reading"]]
    assert row["decoded_values"] == len(candidate)
    assert row["compared_pairs"] == min(len(target), len(candidate))
    assert abs(row["rho"]-corr(candidate, target)) < 1e-8
assert len(result["readings"]) == 14
assert max(abs(row["rho"]) for row in result["readings"]) < 0.12
print("PASS 14 independent pairwise-rank comparisons")
