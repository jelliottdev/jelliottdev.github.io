"""A declared base-60 interpretation of the archived tokens, not a decipherment.

Each original row becomes 64 bits: eight tokens, eight bits per token, MSB first.
No rotations, padding rows, decoder searches or removal of trailing bits.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx"
SOURCE = "exports/alphanumeric-grids.json"
REPORT = "exports/grid-binary-audit.json"


def report():
    source = (ROOT / SOURCE).read_bytes()
    rows = json.loads(source)["records"]
    assert len(ALPHABET) == len(set(ALPHABET)) == 60
    records = []
    for row in rows:
        token = row["token"]
        if len(token) != 2 or any(c not in ALPHABET for c in token):
            raise ValueError(f"Unsupported token {token!r}")
        value = 60 * ALPHABET.index(token[0]) + ALPHABET.index(token[1])
        if not 0 <= value <= 255:
            raise ValueError(f"Token {token!r} does not fit a byte")
        records.append({**row, "value": value, "bits": format(value, "08b")})
    assert len(records) == 256
    bit_rows = []
    for start in range(0, len(records), 8):
        group = records[start:start+8]
        assert len({(r["page"], r["row"]) for r in group}) == 1
        assert [r["column"] for r in group] == list(range(1, 9))
        bit_rows.append("".join(r["bits"] for r in group))
    values = [r["value"] for r in records]
    return {"schema": "liberpedia-grid-binary-audit-v1", "source": SOURCE,
            "source_sha256": hashlib.sha256(source).hexdigest(),
            "alphabet": ALPHABET, "interpretation": "Two-digit base-60 integers, not an established manuscript encoding",
            "bit_order": "Most significant bit first; each token is exactly eight bits",
            "layout": "Original page order 49,50,51; original rows and left-to-right token order",
            "width": 64, "height": 32, "fixed_width_bit_count": 2048,
            "unpadded_bit_count": sum(len(format(v, "b")) for v in values),
            "minimum": min(values), "maximum": max(values),
            "distinct_values": len(set(values)), "value_sum": sum(values),
            "byte_stream_sha256": hashlib.sha256(bytes(values)).hexdigest(),
            "bit_rows": bit_rows, "records": records}


def svg(result):
    # Four device-independent units per bit. White margins are presentation only.
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 288 176" role="img" aria-label="Declared base-60 bytes, original row order, 64 by 32 bits">',
             '<rect width="288" height="176" fill="white"/>',
             '<text x="16" y="14" font-family="sans-serif" font-size="9">64 bits per row · 32 rows · 1 = black</text>',
             '<g fill="black" shape-rendering="crispEdges">']
    for y, row in enumerate(result["bit_rows"]):
        for x, bit in enumerate(row):
            if bit == '1':
                parts.append(f'<rect x="{16+4*x}" y="{24+4*y}" width="4" height="4"/>')
    parts += ['</g>', '<text x="16" y="168" font-family="sans-serif" font-size="9">Declared representation; no barcode decoding performed.</text>', '</svg>']
    return '\n'.join(parts)+'\n'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--svg", type=Path)
    args = parser.parse_args()
    result = report()
    if args.check:
        assert result == json.loads((ROOT / REPORT).read_text(encoding="utf-8"))
        assert svg(result) == (ROOT / "exports/figures/grid-binary.svg").read_text(encoding="utf-8")
        print("PASS: token values, bit rows, source hash and exact SVG")
    for path, content in [(args.output, json.dumps(result, indent=2)+'\n'), (args.svg, svg(result))]:
        if path:
            with path.open('x', encoding='utf-8', newline='\n') as handle:
                handle.write(content)
    if not args.check and not args.output and not args.svg:
        print(json.dumps(result, indent=2))
