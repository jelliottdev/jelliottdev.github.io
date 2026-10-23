#!/usr/bin/env python3
"""Independent reconstruction of the LP2-56 internal-artifact digest table."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
KNOWN_ABC = {
    "sha512": "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f",
    "sha3_512": "b751850b1a57168a5693cd924b6b096e08f621827444f70d884f5d0240d2712e10e116e9192af3c91a7ec57647e3934057340b4cf408d5a56592f8274eec53f0",
    "blake2b_512": "ba80a53f981c4d0d6a2797b69f12f6e94c212f14685ac4b74b12bb6fdbffa2d17d87c5392aab792dc252d5de4533cc9518d38aa8dbf1925ab92386edd4009923",
}


def hash512(name, data):
    h = hashlib.blake2b(data, digest_size=64) if name == "blake2b_512" else hashlib.new(name, data)
    assert h.digest_size == 64
    return h.hexdigest()


def text_versions(s):
    return {
        "exact": s.encode("utf8"),
        "crlf": s.replace("\n", "\r\n").encode("utf8"),
        "drop-final-lf": (s[:-1] if s.endswith("\n") else s).encode("utf8"),
        "one-final-lf": (s.rstrip("\r\n") + "\n").encode("utf8"),
    }


def main():
    for name, wanted in KNOWN_ABC.items():
        assert hash512(name, b"abc") == wanted, name
    manifest_bytes = (HERE / "plan.json").read_bytes()
    m = json.loads(manifest_bytes)
    result = json.loads((HERE / "results.json").read_text(encoding="utf8"))
    assert result["plan_sha256"] == hashlib.sha256(manifest_bytes).hexdigest()
    target_source = json.loads((ROOT / "data/pages/lp2-56.json").read_text(encoding="utf8"))["reading"]["literal"]
    printed = [line.removesuffix("/") for line in target_source.splitlines() if re.fullmatch("[0-9a-f]+/?", line)]
    assert len(printed) == 5 and len("".join(printed)) == 128
    target = "".join(printed)
    assert target == m["target"]["hex"] == result["target"]
    assert len(bytes.fromhex(target)) == result["target_bytes"] == 64
    assert m["algorithms"] == list(KNOWN_ABC)
    assert [x["id"] for x in m["text_variants"]] == list(text_versions(""))

    pages = {}
    inputs = []
    assert len(m["pages"]) == 75
    for item in m["pages"]:
        assert item["id"] not in pages
        for kind in ("page", "image"):
            entry = item[kind]
            data = (ROOT / entry["path"]).read_bytes()
            assert hashlib.sha256(data).hexdigest() == entry["sha256"]
            assert len(data) == entry["size"]
        pages[item["id"]] = json.loads((ROOT / item["page"]["path"]).read_text(encoding="utf8"))
        inputs.append(("image-original", item["id"], "exact", (ROOT / item["image"]["path"]).read_bytes()))
    assert len(pages) == len(list(ROOT.glob("data/pages/lp*.json")))
    assert sum(bool(p["raw"]) for p in pages.values()) == 73
    for item in m["pages"]:
        for version, encoded in text_versions(pages[item["id"]]["raw"]).items():
            inputs.append(("page-raw", item["id"], version, encoded))
    assert len(m["sections"]) == 9
    used = []
    for section in m["sections"]:
        assert section["pages"] == sorted(section["pages"])
        used += section["pages"]
        s = "".join(pages[pid]["reading"]["literal"] for pid in section["pages"])
        assert all(pages[pid]["reading"]["section"] == section["id"] for pid in section["pages"])
        for version, encoded in text_versions(s).items():
            inputs.append(("section-literal", section["id"], version, encoded))
    assert sorted(used) == sorted(pid for pid, p in pages.items() if p.get("reading") and p["reading"].get("section"))
    payload_entry = m["payload"]
    payload = (ROOT / payload_entry["path"]).read_bytes()
    assert len(payload) == payload_entry["size"] == 256
    assert hashlib.sha256(payload).hexdigest() == payload_entry["sha256"]
    inputs.append(("grid-payload", "resolved-256", "exact", payload))
    assert len(inputs) == result["input_variants"] == 412
    assert len({hashlib.sha256(data).hexdigest() for *_, data in inputs}) == result["unique_input_sha256"]

    rows = [json.loads(line) for line in (HERE / "cases.jsonl").read_text(encoding="utf8").splitlines()]
    assert len(rows) == result["digest_comparisons"] == len(inputs) * len(KNOWN_ABC)
    expected = []
    for family, candidate, variant, data in inputs:
        for algorithm in KNOWN_ABC:
            value = hash512(algorithm, data)
            expected.append({"family": family, "candidate": candidate, "variant": variant,
                             "algorithm": algorithm, "bytes": len(data),
                             "input_sha256": hashlib.sha256(data).hexdigest(),
                             "digest": value, "match": value == target})
    assert rows == expected
    assert result["family_comparisons"] == dict(sorted(Counter(row["family"] for row in rows).items()))
    assert result["algorithm_comparisons"] == {a: len(inputs) for a in KNOWN_ABC}
    assert result["matches"] == [row for row in rows if row["match"]]
    assert not result["matches"]
    print(f"Independent check passed: {len(rows)} exact-byte digest rows; zero target matches")


if __name__ == "__main__":
    main()
