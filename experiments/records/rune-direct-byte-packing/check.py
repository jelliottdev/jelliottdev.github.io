"""Independent page-record and byte-prefix audit for direct rune packing."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
report = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
glyph = {row["rune"]: row for row in alphabet}
assert sorted(row["index"] for row in alphabet) == list(range(29))

page_runes = {}
for number in range(56):
    page = f"lp2-{number:02d}"
    record = json.loads((ROOT / "data/pages" / f"{page}.json").read_text(encoding="utf-8"))
    page_runes[page] = [glyph[c] for c in record["raw"] if c in glyph]
    assert len(page_runes[page]) == record["rune_count"]

for entry in report["entries"]:
    target = entry["target"]
    runes = ([r for page in page_runes.values() for r in page]
             if target == "all-lp2-00-55" else page_runes[target])
    if entry["mode"] == "prime-byte":
        payload = bytes(row["prime"] for row in runes)
    else:
        pieces = []
        for row in runes:
            token = [int(bit) for bit in f"{row['index']:05b}"]
            pieces.extend(token[::-1] if entry["mode"] == "index-5-lsb" else token)
        pieces.extend([0] * (-len(pieces) % 8))
        payload = bytes(sum(pieces[pos + bit] << (7-bit) for bit in range(8))
                        for pos in range(0, len(pieces), 8))
    assert len(runes) == entry["runes"]
    assert len(payload) == entry["bytes"]
    assert hashlib.sha256(payload).hexdigest() == entry["sha256"]
    assert payload[:8].hex() == entry["first_8_hex"]
    assert entry["ascii"] == all(b in (9, 10, 13) or 32 <= b <= 126 for b in payload)
    if entry["mode"] == "prime-byte":
        assert max(payload) <= 109 and entry["utf8"]
    for prefix in (bytes.fromhex("89504e470d0a1a0a"), bytes.fromhex("1f8b08"),
                   bytes.fromhex("504b0304"), b"%PDF-", bytes.fromhex("7f454c46"), b"MZ"):
        assert not payload.startswith(prefix)

assert len(report["entries"]) == 3 * report["targets"]
print(f"Independently checked {len(report['entries'])} streams from page records")
