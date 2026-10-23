"""Replay published fixed-width and varint payload/doublet-gap comparisons."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PAYLOAD = ROOT / "experiments/records/grid-page-order-permutations/source/canon_256.bin"
EVENTS = ROOT / "experiments/records/doublet-placement/results.json"
PLAN = HERE / "plan.json"


def ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranked = [0.0] * len(values)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and values[order[end]] == values[order[start]]:
            end += 1
        rank = (start + 1 + end) / 2
        for i in range(start, end):
            ranked[order[i]] = rank
        start = end
    return ranked


def spearman(first, second):
    n = min(len(first), len(second))
    if n < 2:
        return None
    x, y = ranks(first[:n]), ranks(second[:n])
    midpoint = (n + 1) / 2
    numerator = sum((a - midpoint) * (b - midpoint) for a, b in zip(x, y))
    xx = sum((a - midpoint) ** 2 for a in x)
    yy = sum((b - midpoint) ** 2 for b in y)
    return numerator / (xx * yy) ** 0.5 if xx and yy else None


def decode_varint(data, msb_first):
    values = []
    value = 0
    shift = 0
    for byte in data:
        if msb_first:
            value = (value << 7) | (byte & 127)
        else:
            value |= (byte & 127) << shift
            shift += 7
        if byte < 128:
            values.append(value)
            value = shift = 0
    return values


def encode_varint(values, msb_first):
    out = bytearray()
    for value in values:
        parts = []
        while True:
            parts.append(value & 127)
            value >>= 7
            if not value:
                break
        if msb_first:
            parts.reverse()
        out.extend(part | (128 if index < len(parts) - 1 else 0)
                   for index, part in enumerate(parts))
    return bytes(out)


def readings(payload):
    return {
        "uint8": list(payload),
        "uint16_le": list(struct.unpack("<128H", payload)),
        "uint16_be": list(struct.unpack(">128H", payload)),
        "leb128_forward": decode_varint(payload, False),
        "leb128_reverse": decode_varint(payload[::-1], False),
        "msb128_forward": decode_varint(payload, True),
        "msb128_reverse": decode_varint(payload[::-1], True),
    }


def report():
    payload_bytes = PAYLOAD.read_bytes()
    events_bytes = EVENTS.read_bytes()
    assert len(payload_bytes) == 256
    event_data = json.loads(events_bytes)
    starts = [row["global_rune_index_zero_based"] for row in event_data["event_slots"]]
    assert len(starts) == 86 and starts == sorted(starts)
    gaps = [b-a for a, b in zip(starts, starts[1:])]
    targets = {"gaps85": gaps, "first_event_plus_gaps86": [starts[0] + 1] + gaps}
    assert gaps[:4] == [85, 249, 197, 129] and starts[0] + 1 == 122
    for endian in (False, True):
        assert decode_varint(encode_varint(gaps, endian), endian) == gaps
    found = readings(payload_bytes)
    rows = []
    for name, values in found.items():
        for target, actual in targets.items():
            n = min(len(values), len(actual))
            rows.append({"reading": name, "target": target, "decoded_values": len(values),
                         "compared_pairs": n, "rho": round(spearman(values, actual), 8) if n >= 20 else None,
                         "first_five_values": values[:5]})
    # Rotate only the 85-gap target. This preserves its marginal distribution,
    # but shifts are dependent and cannot establish an inferential p-value.
    rotations = []
    for shift in range(len(gaps)):
        shifted = gaps[shift:] + gaps[:shift]
        rotations.append(max(abs(spearman(values, shifted)) for values in found.values()))
    observed = rotations[0]
    output = {
        "schema": "liberpedia-payload-doublet-gaps-v1",
        "input_sha256": {str(PAYLOAD.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(payload_bytes).hexdigest(),
                         str(EVENTS.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(events_bytes).hexdigest(),
                         str(PLAN.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(PLAN.read_bytes()).hexdigest()},
        "event_count": len(starts), "gap_count": len(gaps), "first_event_one_based": starts[0] + 1,
        "first_six_gaps": gaps[:6], "readings": rows,
        "largest_absolute_rho": {"reading": max((r for r in rows if r["rho"] is not None), key=lambda r: abs(r["rho"]))["reading"],
                                 "target": max((r for r in rows if r["rho"] is not None), key=lambda r: abs(r["rho"]))["target"],
                                 "absolute_rho": max(abs(r["rho"]) for r in rows if r["rho"] is not None)},
        "rotation_control_gaps85": {"whole_search_observed_max_absolute_rho": round(observed, 8),
                                    "nonzero_shifts_at_least_observed": sum(v >= observed - 1e-12 for v in rotations[1:]),
                                    "nonzero_shifts": len(rotations) - 1,
                                    "minimum": round(min(rotations[1:]), 8),
                                    "maximum": round(max(rotations[1:]), 8)},
        "positive_control": "All 85 actual gaps round-trip exactly in LEB128 and MSB-first base-128.",
        "limits": "Fixed alignment and source bytes only; circular shifts are a descriptive alignment control, not independent null trials."
    }
    return output


def visual(result):
    fixed = [r for r in result["readings"] if r["target"] == "gaps85"]
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="700" height="400" viewBox="0 0 700 400" role="img" aria-labelledby="title desc">',
             '<title id="title">Payload readings against doublet-gap distances</title>',
             '<desc id="desc">Seven fixed byte readings compared by absolute Spearman correlation to 85 consecutive doublet gaps; all remain below the published 0.5 effect-size gate.</desc>',
             '<rect width="700" height="400" fill="#fff"/>',
             '<g font-family="system-ui,sans-serif" fill="#243847">',
             '<text x="20" y="32" font-size="19">Do the grid bytes track doublet spacing?</text>',
             '<text x="20" y="54" font-size="12">Absolute rank correlation · first 85 gaps, fixed alignment</text>',
             '<line x1="530" y1="73" x2="530" y2="344" stroke="#b35c57" stroke-dasharray="4 4"/>',
             '<text x="536" y="77" font-size="11" fill="#934641">published gate: 0.5</text>']
    labels = {"uint8": "Single bytes", "uint16_le": "16-bit · little endian", "uint16_be": "16-bit · big endian",
              "leb128_forward": "LEB128 · forward", "leb128_reverse": "LEB128 · reverse",
              "msb128_forward": "MSB128 · forward", "msb128_reverse": "MSB128 · reverse"}
    for idx, row in enumerate(fixed):
        y = 105 + idx * 37
        value = abs(row["rho"])
        parts += [f'<text x="20" y="{y}" font-size="13">{labels[row["reading"]]}</text>',
                  f'<rect x="235" y="{y-14}" width="{value*590:.1f}" height="17" fill="#3c718b"/>',
                  f'<text x="{max(243+value*590,250):.1f}" y="{y}" font-size="12">{value:.3f}</text>']
    parts += ['<text x="20" y="382" font-size="11">Exact values, alternate target and controls are in the result table.</text>', '</g></svg>']
    return "\n".join(parts) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = report()
    report_text = json.dumps(output, indent=2) + "\n"
    svg = visual(output)
    if args.write:
        (HERE / "results.json").write_text(report_text, encoding="utf-8", newline="\n")
        (HERE / "gap-correlation.svg").write_text(svg, encoding="utf-8", newline="\n")
    if args.check:
        assert report_text == (HERE / "results.json").read_text(encoding="utf-8")
        assert svg == (HERE / "gap-correlation.svg").read_text(encoding="utf-8")
    print(output["largest_absolute_rho"], output["rotation_control_gaps85"])
