"""Independent, exact-input replay of Dukotah round28/L5 E-02v."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "source"
NAMES = ("canon_256", "canon_256_decpref", "payload_resolved")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode(data, msb):
    found, value, shift = [], 0, 0
    for byte in data:
        if msb:
            value = (value << 7) + (byte & 127)
        else:
            value += (byte & 127) << shift
            shift += 7
        if byte < 128:
            found.append(value)
            value = shift = 0
    return found


def encode(values, msb):
    out = bytearray()
    for value in values:
        pieces = [value & 127]
        value >>= 7
        while value:
            pieces.append(value & 127)
            value >>= 7
        if msb:
            pieces.reverse()
        for index, piece in enumerate(pieces):
            out.append(piece | (128 if index + 1 < len(pieces) else 0))
    return bytes(out)


def ranks(numbers):
    pairs = sorted(enumerate(numbers), key=lambda p: p[1])
    out = [0.0] * len(pairs)
    k = 0
    while k < len(pairs):
        j = k + 1
        while j < len(pairs) and pairs[j][1] == pairs[k][1]:
            j += 1
        midrank = (k + 1 + j) / 2
        for pos in range(k, j):
            out[pairs[pos][0]] = midrank
        k = j
    return out


def rho(left, right):
    x, y = ranks(left), ranks(right)
    mx, my = sum(x) / len(x), sum(y) / len(y)
    numerator = sum((a - mx) * (b - my) for a, b in zip(x, y))
    xx = sum((a - mx) ** 2 for a in x)
    yy = sum((b - my) ** 2 for b in y)
    return numerator / (xx * yy) ** 0.5 if xx and yy else 0.0


def main():
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    for entry in plan["inputs"]:
        path = SRC / Path(entry["path"]).name
        assert digest(path) == entry["sha256"], path
    ciphertext = (SRC / "ct.bin").read_bytes()
    starts = [i for i in range(1, len(ciphertext)) if ciphertext[i] == ciphertext[i - 1]]
    assert len(ciphertext) == 12956 and len(starts) == 86 and starts[0] == 122
    gaps = [b - a for a, b in zip(starts, starts[1:])]
    targets = {"gaps85": gaps, "gaps86_lead122": [starts[0]] + gaps}
    assert gaps[:5] == [85, 249, 197, 129, 127]
    for msb in (False, True):
        planted = encode(gaps, msb)
        assert decode(planted, msb) == gaps
        assert abs(rho(decode(planted, msb), gaps) - 1.0) < 1e-12

    rows = []
    for variant in NAMES:
        payload = (SRC / (variant + ".bin")).read_bytes()
        assert len(payload) == 256
        for encoding, msb, reverse in (("leb128_fwd", False, False),
                                       ("leb128_rev", False, True),
                                       ("msb128_fwd", True, False),
                                       ("msb128_rev", True, True)):
            numbers = decode(payload[::-1] if reverse else payload, msb)
            for target, actual in targets.items():
                n = min(len(numbers), len(actual))
                row = {"variant": variant, "encoding": encoding, "target": target,
                       "decoded_n": len(numbers), "n_used": n}
                if n < 20:
                    row["verdict"] = "undecodable(<20 values)"
                else:
                    row["rho"] = round(rho(numbers[:n], actual[:n]), 4)
                    if abs(row["rho"]) > .5:
                        raise AssertionError("Source p-value phase needed for a gate-crossing row")
                    row["verdict"] = "null"
                rows.append(row)
    archive = json.loads((SRC / "source-results.json").read_text(encoding="utf-8"))
    assert rows == archive["E-02v"], "Source output differs"
    assert archive["controls"]["E-02v"] == {"recovery": 1.0, "neg_hits_50": 0}
    result = {"schema": "liberpedia-source-e02v-replay-v1", "plan_sha256": digest(HERE / "plan.json"),
              "source_revision": "f08b20b632d91209ddbaa747e8e2f23df0c78ba1",
              "source_controls_receipt": archive["controls"]["E-02v"],
              "local_positive": "Both varint orders round-trip all 85 real gaps and yield rho=1.",
              "n_payloads": 3, "n_readings": 12, "n_comparisons": len(rows),
              "maximum_absolute_rho": max(abs(row["rho"]) for row in rows if "rho" in row),
              "rows": rows,
              "interpretation": "All 24 source-defined rows reproduce; none clears the source |rho|>0.5 screen. The conditional 100,000-permutation phase was not entered."}
    with (HERE / "results.json").open("w", encoding="utf-8", newline="\n") as file:
        json.dump(result, file, indent=2, ensure_ascii=False)
        file.write("\n")
    print(f"PASS {len(rows)} source rows; max |rho| {result['maximum_absolute_rho']}")


if __name__ == "__main__":
    main()
