"""Independently rebuild the frozen candidates and scan aligned payload blocks."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CONTROL = b"liberpedia|aligned-digest-blocks|control-v1"
ALGORITHMS = {
    "md5": 16, "sha256": 32, "sha3_256": 32, "blake2s_256": 32,
    "sha512": 64, "sha3_512": 64, "blake2b_512": 64,
}
KNOWN_ABC = {
    "md5": "900150983cd24fb0d6963f7d28e17f72",
    "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
    "sha3_256": "3a985da74fe225b2045c172d6bd390bd855f086e3e9d525b46bfe24511431532",
    "blake2s_256": "508c5e8c327c14e2e1a72ba34eeb452f37458b209ed63a294d999b4c86675982",
    "sha512": "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f",
    "sha3_512": "b751850b1a57168a5693cd924b6b096e08f621827444f70d884f5d0240d2712e10e116e9192af3c91a7ec57647e3934057340b4cf408d5a56592f8274eec53f0",
    "blake2b_512": "ba80a53f981c4d0d6a2797b69f12f6e94c212f14685ac4b74b12bb6fdbffa2d17d87c5392aab792dc252d5de4533cc9518d38aa8dbf1925ab92386edd4009923",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_bytes(name: str, data: bytes) -> bytes:
    if name.startswith("blake2s"):
        return hashlib.blake2s(data).digest()
    if name.startswith("blake2b"):
        return hashlib.blake2b(data).digest()
    return hashlib.new(name, data).digest()


def verify_file(item: dict) -> bytes:
    raw = (ROOT / item["path"]).read_bytes()
    assert len(raw) == item["size"]
    assert sha(raw) == item["sha256"], item["path"]
    return raw


def encoded_forms(text: str) -> dict[str, bytes]:
    return {
        "exact": text.encode("utf-8"),
        "crlf": text.replace("\n", "\r\n").encode("utf-8"),
        "drop-final-lf": text.removesuffix("\n").encode("utf-8"),
        "one-final-lf": (text.rstrip("\r\n") + "\n").encode("utf-8"),
    }


def sorted_matches(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda row: (
        row["algorithm"], row["start_byte"], row["input_sha256"]))


def verify() -> dict:
    plan_raw = (HERE / "plan.json").read_bytes()
    plan = json.loads(plan_raw)
    assert plan["schema"] == "liberpedia-lp2-56-aligned-digest-blocks-plan-v1"
    source_raw = (ROOT / plan["candidate_plan"]["path"]).read_bytes()
    assert sha(source_raw) == plan["candidate_plan"]["sha256"]
    source = json.loads(source_raw)
    assert source["schema"] == "liberpedia-lp2-56-artifact-hash-plan-v1"
    assert plan["payload"] == source["payload"]
    payload = verify_file(source["payload"])
    assert len(payload) == 256
    assert plan["block_rules"]["origin"] == 0
    assert plan["block_rules"]["byte_order"] == "exact output bytes, no reversal"
    assert plan["block_rules"]["windows"] == "non-overlapping complete blocks only"
    assert plan["block_rules"]["lengths"] == [16, 32, 64]
    assert {int(k): names for k, names in plan["algorithms"].items()} == {
        16: ["md5"], 32: ["sha256", "sha3_256", "blake2s_256"],
        64: ["sha512", "sha3_512", "blake2b_512"]}
    assert set(KNOWN_ABC) == set(ALGORITHMS)
    for name, vector in KNOWN_ABC.items():
        assert len(hash_bytes(name, b"abc")) == ALGORITHMS[name]
        assert hash_bytes(name, b"abc").hex() == vector

    pages: dict[str, dict] = {}
    pictures: dict[str, bytes] = {}
    for page in source["pages"]:
        pages[page["id"]] = json.loads(verify_file(page["page"]))
        pictures[page["id"]] = verify_file(page["image"])
    assert [v["id"] for v in source["text_variants"]] == [
        "exact", "crlf", "drop-final-lf", "one-final-lf"]

    reconstructed: list[dict] = []
    unique: dict[bytes, list[str]] = defaultdict(list)

    def collect(family: str, candidate: str, variant: str, raw: bytes) -> None:
        reconstructed.append({"family": family, "candidate": candidate,
                              "variant": variant, "input_sha256": sha(raw), "bytes": len(raw)})
        unique[raw].append(f"{family}/{candidate}/{variant}")

    for page in source["pages"]:
        collect("image-original", page["id"], "exact", pictures[page["id"]])
    for page in source["pages"]:
        for variant, raw in encoded_forms(pages[page["id"]]["raw"]).items():
            collect("page-raw", page["id"], variant, raw)
    for section in source["sections"]:
        literal = "".join(pages[pid]["reading"]["literal"] for pid in section["pages"])
        for variant, raw in encoded_forms(literal).items():
            collect("section-literal", section["id"], variant, raw)
    collect("grid-payload", "resolved-256", "exact", payload)
    assert len(reconstructed) == 412 == plan["candidate_plan"]["variants"]
    assert len(unique) == 324 == plan["candidate_plan"]["unique_byte_strings"]

    candidate_map_raw = (HERE / "candidate-map.json").read_bytes()
    assert json.loads(candidate_map_raw) == reconstructed
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert result["candidate_map_sha256"] == sha(candidate_map_raw)
    assert result["plan_sha256"] == sha(plan_raw)
    assert result["candidate_plan_sha256"] == sha(source_raw)
    assert result["payload_sha256"] == sha(payload)

    # The checker reverses the main runner's search direction: index all candidate
    # digests first, then ask each payload block whether it appears in the index.
    index: dict[str, dict[bytes, list[tuple[bytes, list[str]]]]] = {}
    for name in ALGORITHMS:
        values: dict[bytes, list[tuple[bytes, list[str]]]] = defaultdict(list)
        for raw, aliases in unique.items():
            values[hash_bytes(name, raw)].append((raw, aliases))
        index[name] = values

    matches: list[dict] = []
    comparisons: dict[str, int] = {}
    for name, size in ALGORITHMS.items():
        assert 256 % size == 0
        comparisons[name] = len(unique) * (256 // size)
        for block_index in range(256 // size):
            start = block_index * size
            block = payload[start:start + size]
            for raw, aliases in index[name].get(block, []):
                matches.append({"algorithm": name, "block_bytes": size,
                                "block_index": block_index, "start_byte": start,
                                "end_byte_exclusive": start + size,
                                "input_sha256": sha(raw), "aliases": aliases,
                                "digest_hex": block.hex()})
    assert sum(comparisons.values()) == 16848 == 324 * 52
    assert sorted_matches(result["matches"]) == sorted_matches(matches)
    assert result["algorithm_comparisons"] == dict(sorted(comparisons.items()))
    assert result["comparisons"] == sum(comparisons.values())
    assert result["digest_computations"] == 324 * 7
    assert result["candidate_variants"] == 412
    assert result["unique_candidate_bytes"] == 324
    assert result["aligned_blocks_by_size"] == {"16": 16, "32": 8, "64": 4}
    assert result["payload_bytes"] == 256

    controls = []
    for name, size in ALGORITHMS.items():
        value = hash_bytes(name, CONTROL)
        box = value + b"\xa7" * (256 - 2 * size) + value
        found = [offset for offset in range(0, 256, size)
                 if box[offset:offset + size] == value]
        reverse = [offset for offset in range(0, 256, size)
                   if box[offset:offset + size] == value[::-1]]
        assert found == [0, 256 - size] and not reverse
        controls.append({"algorithm": name, "block_bytes": size,
                         "planted_offsets": found, "reversed_digest_offsets": reverse})
    assert result["synthetic_controls"] == controls
    return {"candidate_variants": len(reconstructed), "unique_bytes": len(unique),
            "aligned_comparisons": sum(comparisons.values()),
            "matches": len(matches), "positive_controls": len(controls)}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
