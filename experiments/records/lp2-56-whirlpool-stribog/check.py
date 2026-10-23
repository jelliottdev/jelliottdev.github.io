#!/usr/bin/env python3
"""Independent byte-corpus reconstruction with libgcrypt's streaming digest API."""
import argparse
import ctypes
import ctypes.util
import hashlib
import json
import os
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def gcrypt(path):
    if path and Path(path).exists():
        handle = os.add_dll_directory(str(Path(path).parent)) if os.name == "nt" else None
        dll = ctypes.CDLL(str(path))
    else:
        found = ctypes.util.find_library("gcrypt")
        if not found:
            raise RuntimeError("libgcrypt unavailable; supply --libgcrypt")
        handle = None
        dll = ctypes.CDLL(found)
    dll.gcry_md_map_name.argtypes = [ctypes.c_char_p]
    dll.gcry_md_map_name.restype = ctypes.c_int
    dll.gcry_md_get_algo_dlen.argtypes = [ctypes.c_int]
    dll.gcry_md_get_algo_dlen.restype = ctypes.c_uint
    dll.gcry_md_open.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_int, ctypes.c_uint]
    dll.gcry_md_open.restype = ctypes.c_uint
    dll.gcry_md_write.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]
    dll.gcry_md_read.argtypes = [ctypes.c_void_p, ctypes.c_int]
    dll.gcry_md_read.restype = ctypes.c_void_p
    dll.gcry_md_close.argtypes = [ctypes.c_void_p]
    return dll, handle


def stream_hash(lib, name, data):
    algo = lib.gcry_md_map_name(name.encode("ascii"))
    if not algo or lib.gcry_md_get_algo_dlen(algo) != 64:
        raise RuntimeError(f"Missing 512-bit algorithm {name}")
    context = ctypes.c_void_p()
    error = lib.gcry_md_open(ctypes.byref(context), algo, 0)
    if error:
        raise RuntimeError(f"gcry_md_open failed: {name}: {error}")
    try:
        source = ctypes.create_string_buffer(data)
        lib.gcry_md_write(context, source, len(data))
        return ctypes.string_at(lib.gcry_md_read(context, algo), 64)
    finally:
        lib.gcry_md_close(context)


def all_inputs(pinned):
    candidates = []
    parsed = {}
    assert len(pinned["pages"]) == 75
    for page in pinned["pages"]:
        for kind in ("page", "image"):
            evidence = page[kind]
            raw = (ROOT / evidence["path"]).read_bytes()
            assert len(raw) == evidence["size"]
            assert hashlib.sha256(raw).hexdigest() == evidence["sha256"]
        parsed[page["id"]] = json.loads((ROOT / page["page"]["path"]).read_text(encoding="utf8"))
        candidates.append(("image-original", page["id"], "exact", (ROOT / page["image"]["path"]).read_bytes()))
    variants = [v["id"] for v in pinned["text_variants"]]
    assert variants == ["exact", "crlf", "drop-final-lf", "one-final-lf"]

    def encodings(s):
        return {"exact": s.encode("utf8"),
                "crlf": s.replace("\n", "\r\n").encode("utf8"),
                "drop-final-lf": (s[:-1] if s.endswith("\n") else s).encode("utf8"),
                "one-final-lf": (s.rstrip("\r\n") + "\n").encode("utf8")}

    for page in pinned["pages"]:
        for label, b in encodings(parsed[page["id"]]["raw"]).items():
            candidates.append(("page-raw", page["id"], label, b))
    assert len(pinned["sections"]) == 9
    for section in pinned["sections"]:
        assert section["pages"] == sorted(section["pages"])
        literal = "".join(parsed[pid]["reading"]["literal"] for pid in section["pages"])
        for label, b in encodings(literal).items():
            candidates.append(("section-literal", section["id"], label, b))
    item = pinned["payload"]
    payload = (ROOT / item["path"]).read_bytes()
    assert len(payload) == item["size"] == 256
    assert hashlib.sha256(payload).hexdigest() == item["sha256"]
    candidates.append(("grid-payload", "resolved-256", "exact", payload))
    assert len(candidates) == 412
    return candidates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--libgcrypt")
    args = parser.parse_args()
    frozen_bytes = (HERE / "plan.json").read_bytes()
    frozen = json.loads(frozen_bytes)
    old_bytes = (ROOT / frozen["source_plan"]["path"]).read_bytes()
    assert hashlib.sha256(old_bytes).hexdigest() == frozen["source_plan"]["sha256"]
    old = json.loads(old_bytes)
    saved = json.loads((HERE / "results.json").read_text(encoding="utf8"))
    assert saved["plan_sha256"] == hashlib.sha256(frozen_bytes).hexdigest()
    assert saved["source_plan_sha256"] == frozen["source_plan"]["sha256"]
    page56 = json.loads((ROOT / "data/pages/lp2-56.json").read_text(encoding="utf8"))["reading"]["literal"]
    rows = [line.rstrip("/") for line in page56.splitlines() if re.fullmatch("[0-9a-f]+/?", line)]
    target = "".join(rows)
    assert len(rows) == 5 and len(target) == 128
    assert target == frozen["target"]["hex"] == saved["target"] == old["target"]["hex"]
    candidates = all_inputs(old)
    distinct = {hashlib.sha256(b).hexdigest(): b for *_, b in candidates}
    assert len(distinct) == saved["unique_input_sha256"] == 324
    path = args.libgcrypt or frozen["library"]["local_path"]
    lib, handle = gcrypt(path)
    names = {a["id"]: a["libgcrypt_name"] for a in frozen["algorithms"]}
    assert names == {"whirlpool": "WHIRLPOOL", "stribog512": "STRIBOG512"}
    for control in frozen["controls"]:
        data = bytes.fromhex(control["input_hex"])
        expected = bytes.fromhex(control["expected_hex"])
        if control["algorithm"] == "stribog512":
            data, expected = data[::-1], expected[::-1]
        assert stream_hash(lib, names[control["algorithm"]], data) == expected, control["id"]
    computed = {(identity, name): stream_hash(lib, name, data)
                for identity, data in distinct.items() for name in names.values()}
    expected_cases = []
    for family, candidate, variant, b in candidates:
        identity = hashlib.sha256(b).hexdigest()
        for algorithm in frozen["algorithms"]:
            raw = computed[(identity, algorithm["libgcrypt_name"])]
            for display in algorithm["digest_display"]:
                rendered = raw.hex() if display == "byte-order" else raw[::-1].hex()
                expected_cases.append({"family": family, "candidate": candidate, "variant": variant,
                                       "input_sha256": identity, "bytes": len(b),
                                       "algorithm": algorithm["id"], "display": display,
                                       "digest": rendered, "match": rendered == target})
    published_cases = [json.loads(line) for line in (HERE / "cases.jsonl").read_text(encoding="utf8").splitlines()]
    assert published_cases == expected_cases
    assert len(published_cases) == saved["digest_display_comparisons"] == 1236
    assert saved["unique_digest_operations"] == len(distinct) * len(names) == 648
    assert saved["family_comparisons"] == dict(sorted(Counter(c["family"] for c in published_cases).items()))
    assert saved["algorithm_display_comparisons"] == {f"{a['id']}:{d}": 412 for a in frozen["algorithms"] for d in a["digest_display"]}
    assert saved["control_vectors_passed"] == [x["id"] for x in frozen["controls"]]
    assert saved["matches"] == [c for c in published_cases if c["match"]] == []
    _ = handle
    print("Independent streaming-API check passed: 648 unique digests, 1,236 displayed comparisons, zero matches")


if __name__ == "__main__":
    main()
