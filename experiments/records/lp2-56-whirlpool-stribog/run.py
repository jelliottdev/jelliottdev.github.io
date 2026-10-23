#!/usr/bin/env python3
"""Hash the frozen LP2-56 artifact byte corpus with installed libgcrypt."""
import argparse
import ctypes
import ctypes.util
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load_library(path):
    if path:
        library_path = Path(path)
        if not library_path.exists():
            raise FileNotFoundError(library_path)
        if os.name == "nt":
            # Keep this object alive while the DLL and its dependencies are loaded.
            dll_directory = os.add_dll_directory(str(library_path.parent))
        else:
            dll_directory = None
        g = ctypes.CDLL(str(library_path))
    else:
        library_path = ctypes.util.find_library("gcrypt")
        if not library_path:
            raise RuntimeError("libgcrypt not found; provide --libgcrypt")
        dll_directory = None
        g = ctypes.CDLL(library_path)
    g.gcry_check_version.argtypes = [ctypes.c_char_p]
    g.gcry_check_version.restype = ctypes.c_char_p
    g.gcry_md_map_name.argtypes = [ctypes.c_char_p]
    g.gcry_md_map_name.restype = ctypes.c_int
    g.gcry_md_get_algo_dlen.argtypes = [ctypes.c_int]
    g.gcry_md_get_algo_dlen.restype = ctypes.c_uint
    g.gcry_md_hash_buffer.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]
    g.gcry_md_hash_buffer.restype = None
    return g, dll_directory, str(library_path), g.gcry_check_version(None).decode("ascii")


def hash_buffer(g, name, data):
    algorithm = g.gcry_md_map_name(name.encode("ascii"))
    if not algorithm or g.gcry_md_get_algo_dlen(algorithm) != 64:
        raise RuntimeError(f"{name} unavailable or not 64 bytes")
    out = (ctypes.c_ubyte * 64)()
    buffer = ctypes.create_string_buffer(data)
    g.gcry_md_hash_buffer(algorithm, out, buffer, len(data))
    return bytes(out)


def verify_controls(g, plan):
    names = {a["id"]: a["libgcrypt_name"] for a in plan["algorithms"]}
    for control in plan["controls"]:
        message = bytes.fromhex(control["input_hex"])
        expected = bytes.fromhex(control["expected_hex"])
        if control["algorithm"] == "stribog512":
            message = message[::-1]
            expected = expected[::-1]
        actual = hash_buffer(g, names[control["algorithm"]], message)
        if actual != expected:
            raise AssertionError(f"libgcrypt vector failed: {control['id']}")


def encoded(value, variant):
    if variant == "exact":
        pass
    elif variant == "crlf":
        value = value.replace("\n", "\r\n")
    elif variant == "drop-final-lf":
        value = value[:-1] if value.endswith("\n") else value
    elif variant == "one-final-lf":
        value = value.rstrip("\r\n") + "\n"
    else:
        raise ValueError(variant)
    return value.encode("utf8")


def inputs(old_plan):
    assert [v["id"] for v in old_plan["text_variants"]] == ["exact", "crlf", "drop-final-lf", "one-final-lf"]
    pages = {}
    rows = []
    for p in old_plan["pages"]:
        for name in ("page", "image"):
            entry = p[name]
            data = (ROOT / entry["path"]).read_bytes()
            assert len(data) == entry["size"] and hashlib.sha256(data).hexdigest() == entry["sha256"]
        pages[p["id"]] = json.loads((ROOT / p["page"]["path"]).read_text(encoding="utf8"))
        rows.append(("image-original", p["id"], "exact", (ROOT / p["image"]["path"]).read_bytes()))
    for p in old_plan["pages"]:
        for variant in old_plan["text_variants"]:
            rows.append(("page-raw", p["id"], variant["id"], encoded(pages[p["id"]]["raw"], variant["id"])))
    for section in old_plan["sections"]:
        text = "".join(pages[pid]["reading"]["literal"] for pid in section["pages"])
        for variant in old_plan["text_variants"]:
            rows.append(("section-literal", section["id"], variant["id"], encoded(text, variant["id"])))
    payload_entry = old_plan["payload"]
    payload = (ROOT / payload_entry["path"]).read_bytes()
    assert len(payload) == payload_entry["size"] == 256
    assert hashlib.sha256(payload).hexdigest() == payload_entry["sha256"]
    rows.append(("grid-payload", "resolved-256", "exact", payload))
    assert len(rows) == 412
    return rows


def build(libpath=None):
    plan_bytes = (HERE / "plan.json").read_bytes()
    plan = json.loads(plan_bytes)
    assert plan["schema"] == "liberpedia-lp2-56-whirlpool-stribog-plan-v1"
    old_bytes = (ROOT / plan["source_plan"]["path"]).read_bytes()
    assert hashlib.sha256(old_bytes).hexdigest() == plan["source_plan"]["sha256"]
    old = json.loads(old_bytes)
    assert old["target"] == plan["target"] and len(bytes.fromhex(plan["target"]["hex"])) == 64
    source_inputs = inputs(old)
    unique = {hashlib.sha256(data).hexdigest(): data for _, _, _, data in source_inputs}
    assert len(unique) == 324
    selected = libpath or (plan["library"]["local_path"] if Path(plan["library"]["local_path"]).exists() else None)
    g, dll_directory, used_path, version = load_library(selected)
    if selected == plan["library"]["local_path"]:
        assert hashlib.sha256(Path(selected).read_bytes()).hexdigest() == plan["library"]["sha256"]
        assert version == plan["library"]["version"]
    verify_controls(g, plan)
    hashed = {}
    for identity, data in unique.items():
        hashed[identity] = {a["id"]: hash_buffer(g, a["libgcrypt_name"], data) for a in plan["algorithms"]}
    target = plan["target"]["hex"]
    cases = []
    for family, candidate, variant, data in source_inputs:
        identity = hashlib.sha256(data).hexdigest()
        for algorithm in plan["algorithms"]:
            digest = hashed[identity][algorithm["id"]]
            for display in algorithm["digest_display"]:
                value = digest.hex() if display == "byte-order" else digest[::-1].hex()
                cases.append({"family": family, "candidate": candidate, "variant": variant,
                              "input_sha256": identity, "bytes": len(data),
                              "algorithm": algorithm["id"], "display": display,
                              "digest": value, "match": value == target})
    summary = {"schema": "liberpedia-lp2-56-whirlpool-stribog-results-v1",
               "plan_sha256": hashlib.sha256(plan_bytes).hexdigest(),
               "source_plan_sha256": hashlib.sha256(old_bytes).hexdigest(),
               "target": target, "target_bytes": 64,
               "input_variants": len(source_inputs), "unique_input_sha256": len(unique),
               "unique_digest_operations": len(unique) * len(plan["algorithms"]),
               "digest_display_comparisons": len(cases),
               "family_comparisons": dict(sorted(Counter(c["family"] for c in cases).items())),
               "algorithm_display_comparisons": {f"{a['id']}:{display}": sum(c["algorithm"] == a["id"] and c["display"] == display for c in cases)
                                                 for a in plan["algorithms"] for display in a["digest_display"]},
               "control_vectors_passed": [x["id"] for x in plan["controls"]],
               "matches": [x for x in cases if x["match"]]}
    # Runtime information is informational, not part of deterministic published data.
    print(f"libgcrypt {version} at {used_path}; {summary['unique_digest_operations']} unique digests")
    _ = dll_directory
    return cases, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--libgcrypt", help="Path to another installed libgcrypt; verified against the same vectors")
    args = parser.parse_args()
    cases, summary = build(args.libgcrypt)
    with (HERE / "cases.jsonl").open("w", encoding="utf8", newline="\n") as out:
        for case in cases:
            out.write(json.dumps(case, sort_keys=True) + "\n")
    (HERE / "results.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf8")
    print(f"{summary['digest_display_comparisons']} full-target comparisons; {len(summary['matches'])} matches")


if __name__ == "__main__":
    main()
