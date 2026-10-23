"""Screen three fixed, direct LP2 rune-to-byte encodings."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PAGES = [f"lp2-{i:02d}" for i in range(56)]
SIGNATURES = {
    "PNG": bytes.fromhex("89504e470d0a1a0a"),
    "gzip": bytes.fromhex("1f8b08"),
    "ZIP": bytes.fromhex("504b0304"),
    "PDF": b"%PDF-",
    "ELF": bytes.fromhex("7f454c46"),
    "PE": b"MZ",
}


def data():
    index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
    lookup = {row["rune"]: (row["index"], row["prime"]) for row in index["alphabet"]}
    assert len(lookup) == 29 and max(p for _, p in lookup.values()) == 109
    pages = {}
    hashes = {}
    for page in PAGES:
        path = f"text/{page}.txt"
        raw = (ROOT / path).read_bytes()
        hashes[path] = hashlib.sha256(raw).hexdigest()
        text = raw.decode("utf-8")
        unknown = {ch for ch in text if "\u16a0" <= ch <= "\u16ff" and ch not in lookup}
        if unknown:
            raise ValueError(f"Unknown rune on {page}: {unknown!r}")
        pages[page] = [lookup[ch] for ch in text if ch in lookup]
        expected = next(row["rune_count"] for row in index["pages"] if row["id"] == page)
        assert len(pages[page]) == expected, (page, len(pages[page]), expected)
    hashes["data/index.json"] = hashlib.sha256((ROOT / "data/index.json").read_bytes()).hexdigest()
    return pages, hashes


def pack_five(indices, reverse_token_bits=False):
    bits = "".join((f"{n:05b}"[::-1] if reverse_token_bits else f"{n:05b}") for n in indices)
    bits += "0" * (-len(bits) % 8)
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))


def encode(runes, mode):
    if mode == "prime-byte":
        return bytes(prime for _, prime in runes)
    return pack_five([idx for idx, _ in runes], mode == "index-5-lsb")


def screen(raw):
    if not raw:
        return {"ascii": False, "utf8": False, "signature": []}
    try:
        raw.decode("utf-8")
        utf8 = True
    except UnicodeDecodeError:
        utf8 = False
    return {
        "ascii": all(byte in (9, 10, 13) or 32 <= byte <= 126 for byte in raw),
        "utf8": utf8,
        "signature": [name for name, prefix in SIGNATURES.items() if raw.startswith(prefix)],
    }


def calculate():
    pages, hashes = data()
    modes = ["index-5-msb", "index-5-lsb", "prime-byte"]
    streams = {"all-lp2-00-55": [rune for page in PAGES for rune in pages[page]]}
    streams.update({page: pages[page] for page in PAGES if pages[page]})
    entries = []
    for name, runes in streams.items():
        for mode in modes:
            raw = encode(runes, mode)
            entries.append({"target": name, "mode": mode, "runes": len(runes), "bytes": len(raw),
                            "sha256": hashlib.sha256(raw).hexdigest(), "first_8_hex": raw[:8].hex(), **screen(raw)})
    assert screen(b"MZexample")["signature"] == ["PE"]
    assert screen(b"plain text")["ascii"] and screen(b"plain text")["utf8"]
    assert all(screen(prefix + b"test")["signature"] == [name] for name, prefix in SIGNATURES.items())
    assert pack_five([0, 1, 2, 3]) == bytes.fromhex("004430")
    return {"schema": "liberpedia-rune-direct-byte-packing-v1", "inputs_sha256": hashes,
            "modes": modes, "targets": len(streams), "screens": list(SIGNATURES), "entries": entries,
            "passes": {mode: {"ascii": sum(e["ascii"] for e in entries if e["mode"] == mode),
                               "utf8": sum(e["utf8"] for e in entries if e["mode"] == mode),
                               "signatures": sum(bool(e["signature"]) for e in entries if e["mode"] == mode)}
                       for mode in modes}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = calculate()
    output = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    path = HERE / "results.json"
    if args.check:
        assert path.read_text(encoding="utf-8") == output
        print(f"Verified {len(result['entries'])} direct byte streams")
    else:
        path.write_text(output, encoding="utf-8", newline="\n")
        print(result["passes"])


if __name__ == "__main__":
    main()
