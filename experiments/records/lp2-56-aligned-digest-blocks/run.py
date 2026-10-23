"""Check complete, aligned digest-size blocks of the resolved LP2 grid payload."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CONTROL_INPUT = b"liberpedia|aligned-digest-blocks|control-v1"
ABC_VECTORS = {
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


def digest(algorithm: str, data: bytes) -> bytes:
    if algorithm == "blake2s_256":
        return hashlib.blake2s(data, digest_size=32).digest()
    if algorithm == "blake2b_512":
        return hashlib.blake2b(data, digest_size=64).digest()
    return getattr(hashlib, algorithm)(data).digest()


def text_bytes(value: str, variant: str) -> bytes:
    if variant == "crlf":
        value = value.replace("\n", "\r\n")
    elif variant == "drop-final-lf":
        value = value[:-1] if value.endswith("\n") else value
    elif variant == "one-final-lf":
        value = value.rstrip("\r\n") + "\n"
    elif variant != "exact":
        raise ValueError(variant)
    return value.encode("utf-8")


def checked_bytes(entry: dict) -> bytes:
    raw = (ROOT / entry["path"]).read_bytes()
    assert len(raw) == entry["size"] and sha(raw) == entry["sha256"], entry["path"]
    return raw


def load_inputs() -> tuple[dict, bytes, list[tuple[str, str, str, bytes]]]:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    assert plan["schema"] == "liberpedia-lp2-56-aligned-digest-blocks-plan-v1"
    source_plan_bytes = (ROOT / plan["candidate_plan"]["path"]).read_bytes()
    assert sha(source_plan_bytes) == plan["candidate_plan"]["sha256"]
    source = json.loads(source_plan_bytes)
    assert source["schema"] == "liberpedia-lp2-56-artifact-hash-plan-v1"
    assert source["payload"] == plan["payload"]
    payload = checked_bytes(plan["payload"])
    assert len(payload) == 256
    assert plan["block_rules"] == {
        "origin": 0, "byte_order": "exact output bytes, no reversal",
        "windows": "non-overlapping complete blocks only", "lengths": [16, 32, 64]}

    pages: dict[str, dict] = {}
    image_bytes: dict[str, bytes] = {}
    for entry in source["pages"]:
        pages[entry["id"]] = json.loads(checked_bytes(entry["page"]))
        image_bytes[entry["id"]] = checked_bytes(entry["image"])
    variants = [v["id"] for v in source["text_variants"]]
    assert variants == ["exact", "crlf", "drop-final-lf", "one-final-lf"]

    inputs: list[tuple[str, str, str, bytes]] = []
    for entry in source["pages"]:
        inputs.append(("image-original", entry["id"], "exact", image_bytes[entry["id"]]))
    for entry in source["pages"]:
        for variant in variants:
            inputs.append(("page-raw", entry["id"], variant,
                           text_bytes(pages[entry["id"]]["raw"], variant)))
    for section in source["sections"]:
        literal = "".join(pages[pid]["reading"]["literal"] for pid in section["pages"])
        for variant in variants:
            inputs.append(("section-literal", section["id"], variant,
                           text_bytes(literal, variant)))
    inputs.append(("grid-payload", "resolved-256", "exact", payload))
    assert len(inputs) == plan["candidate_plan"]["variants"] == 412
    return plan, payload, inputs


def aligned_hits(container: bytes, value: bytes) -> list[int]:
    size = len(value)
    assert len(container) == 256 and 256 % size == 0
    return [start for start in range(0, 256, size)
            if container[start:start + size] == value]


def build() -> tuple[list[dict], dict]:
    plan, payload, inputs = load_inputs()
    algorithms = {int(size): names for size, names in plan["algorithms"].items()}
    assert algorithms == {
        16: ["md5"], 32: ["sha256", "sha3_256", "blake2s_256"],
        64: ["sha512", "sha3_512", "blake2b_512"]}
    for algorithm, expected in ABC_VECTORS.items():
        assert digest(algorithm, b"abc").hex() == expected

    candidate_map: list[dict] = []
    unique: dict[str, tuple[bytes, list[str]]] = {}
    for family, candidate, variant, raw in inputs:
        key = sha(raw)
        label = f"{family}/{candidate}/{variant}"
        candidate_map.append({"family": family, "candidate": candidate,
                              "variant": variant, "input_sha256": key, "bytes": len(raw)})
        if key in unique:
            assert unique[key][0] == raw, "SHA-256 collision in candidate inventory"
            unique[key][1].append(label)
        else:
            unique[key] = (raw, [label])
    assert len(unique) == plan["candidate_plan"]["unique_byte_strings"] == 324

    blocks = {size: [(start, payload[start:start + size])
                     for start in range(0, 256, size)] for size in algorithms}
    assert {size: len(items) for size, items in blocks.items()} == {16: 16, 32: 8, 64: 4}
    comparisons = Counter()
    matches: list[dict] = []
    for key, (raw, aliases) in unique.items():
        for size, names in algorithms.items():
            for algorithm in names:
                value = digest(algorithm, raw)  # once per candidate and algorithm
                assert len(value) == size
                for start, block in blocks[size]:
                    comparisons[algorithm] += 1
                    if value == block:
                        matches.append({"algorithm": algorithm, "block_bytes": size,
                                        "block_index": start // size, "start_byte": start,
                                        "end_byte_exclusive": start + size,
                                        "input_sha256": key, "aliases": aliases,
                                        "digest_hex": value.hex()})

    controls = []
    for size, names in algorithms.items():
        for algorithm in names:
            value = digest(algorithm, CONTROL_INPUT)
            planted = bytearray(b"\xa7" * 256)
            planted[:size] = value
            planted[256 - size:] = value
            locations = aligned_hits(bytes(planted), value)
            assert locations == [0, 256 - size]
            reversed_locations = aligned_hits(bytes(planted), value[::-1])
            assert not reversed_locations and value != value[::-1]
            controls.append({"algorithm": algorithm, "block_bytes": size,
                             "planted_offsets": locations,
                             "reversed_digest_offsets": reversed_locations})

    assert sum(comparisons.values()) == 324 * 52 == 16848
    assert len(controls) == 7
    map_bytes = (json.dumps(candidate_map, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    result = {
        "schema": "liberpedia-lp2-56-aligned-digest-blocks-results-v1",
        "plan_sha256": sha((HERE / "plan.json").read_bytes()),
        "candidate_plan_sha256": plan["candidate_plan"]["sha256"],
        "payload_sha256": plan["payload"]["sha256"],
        "payload_bytes": len(payload),
        "candidate_variants": len(candidate_map),
        "unique_candidate_bytes": len(unique),
        "digest_computations": len(unique) * len(ABC_VECTORS),
        "aligned_blocks_by_size": {str(size): len(items) for size, items in blocks.items()},
        "algorithm_comparisons": dict(sorted(comparisons.items())),
        "comparisons": sum(comparisons.values()),
        "matches": matches,
        "synthetic_controls": controls,
        "candidate_map_sha256": sha(map_bytes),
    }
    return candidate_map, result


def main() -> None:
    candidate_map, result = build()
    map_bytes = (json.dumps(candidate_map, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    result_bytes = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if sys.argv[1:] == ["--write"]:
        (HERE / "candidate-map.json").write_bytes(map_bytes)
        (HERE / "results.json").write_bytes(result_bytes)
    elif not sys.argv[1:] or sys.argv[1:] == ["--check"]:
        assert (HERE / "candidate-map.json").read_bytes() == map_bytes
        assert (HERE / "results.json").read_bytes() == result_bytes
    else:
        raise SystemExit("usage: run.py [--check|--write]")
    print(f"{result['candidate_variants']} variants; {result['unique_candidate_bytes']} unique bytes; "
          f"{result['comparisons']} aligned comparisons; {len(result['matches'])} matches; "
          f"{len(result['synthetic_controls'])} planted controls passed")


if __name__ == "__main__":
    main()
