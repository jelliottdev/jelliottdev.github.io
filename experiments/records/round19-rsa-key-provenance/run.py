"""Replay the pinned Round 19 C1 E-01 arithmetic from its minimal witnesses."""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "source"
ROOT = HERE.parents[2]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def replay():
    plan = json.loads((HERE / "plan.json").read_text())
    for item in plan["inputs"]:
        path = ROOT / item["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], path

    em = load_module("extract_moduli", SRC / "extract_moduli.py")
    source = load_module("e01_rsa", SRC / "e01_rsa.py")
    historical = json.loads((SRC / "out_e01.json").read_text())
    original = json.loads((SRC / "moduli.json").read_text())
    witness_map = json.loads((SRC / "witness-map.json").read_text())
    extracted = {}
    witnessed = {}
    for source_path, rel in witness_map.items():
        data = (SRC / rel).read_text(encoding="utf-8", errors="replace")
        for packet in em.dearmor(data):
            for tag, body in em.packets(packet):
                if tag not in (6, 14):
                    continue
                key = em.parse_key_packet(body)
                if key:
                    fp = key["fingerprint"]
                    if fp in extracted:
                        assert extracted[fp]["n"] == key["n"]
                    extracted[fp] = key
                    witnessed.setdefault(fp, []).append(source_path)
    assert len(extracted) == 22

    moduli = {}
    for row in original["pgp_moduli"]:
        fp = row["fingerprint"]
        assert extracted[fp]["n"] == int(row["n_hex"], 16)
        moduli[fp] = (extracted[fp]["n"], extracted[fp]["e"])
    for fp, key in extracted.items():
        moduli[fp] = (key["n"], key["e"])
    modulus_by_name = {}
    for row in historical["moduli_tested"]:
        fp = row["fingerprint"]
        if fp:
            n, e = moduli[fp]
            assert n.bit_length() == row["bits"] and e == row["e_published"]
        else:
            item = next(x for x in original["other_moduli"] if x["name"] == row["name"])
            n, e = int(item["n_hex"], 16), item["e"]
        modulus_by_name[row["name"]] = (n, e)

    payloads = {name: (SRC / f"{name}.bin").read_bytes() for name in historical["payload_variants"]}
    rows = []
    for payload_name, data in payloads.items():
        assert len(data) == 256
        for endian in ("big", "little"):
            number = int.from_bytes(data, endian)
            for entry in historical["moduli_tested"]:
                n, published_e = modulus_by_name[entry["name"]]
                klen = (n.bit_length() + 7) // 8
                aligns = [("right", number)]
                if klen > len(data):
                    aligns.append(("left", number << (8 * (klen - len(data)))))
                for align, value in aligns:
                    for exponent in sorted(set([65537, 3, 17, published_e])):
                        row = {"payload": payload_name, "endian": endian,
                               "align": align, "modulus": entry["name"],
                               "modulus_bits": n.bit_length(), "e": exponent}
                        if value >= n:
                            row["verdict"] = "SKIP"
                            row["why"] = ("s >= n: a signature/ciphertext under this "
                                          "modulus is %d bytes, the payload is %d" % (klen, len(data)))
                        else:
                            power = pow(value, exponent, n)
                            block = power.to_bytes(klen, "big")
                            embits = n.bit_length() - 1
                            emlen = (embits + 7) // 8
                            block2 = (power % (1 << embits)).to_bytes(emlen, "big")
                            hits = source.all_matchers(block, n.bit_length())
                            hits += [x for x in (source.match_pss(block2, embits, hn, hf)
                                                  for hn, hf in source.HASHES.items()) if x]
                            row["head_hex"] = block[:12].hex()
                            row["entropy_bits_per_byte"] = round(source.entropy(block), 3)
                            row["printable_ratio"] = round(sum(32 <= b < 127 for b in block) / len(block), 3)
                            row["verdict"] = "HIT" if hits else "NULL"
                            if hits:
                                row["structures"] = hits
                        rows.append(row)
    assert rows == historical["rows"]
    assert len(rows) == 738
    related = {x["fingerprint"] for x in original["pgp_moduli"]}
    key_class = {fp: ("Cicada PGP key" if fp in related else "other archived key")
                 for fp in extracted}
    summary = {
        "schema": "liberpedia-round19-rsa-provenance-v1",
        "source_revision": plan["source_revision"],
        "plan_sha256": hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest(),
        "source_row_match": True,
        "named_moduli": len(modulus_by_name),
        "pgp_packets": len(extracted),
        "cicada_pgp_packets": len(related),
        "other_archived_pgp_packets": len(extracted) - len(related),
        "all_named_rows": len(rows),
        "evaluated_rows": sum(r["verdict"] != "SKIP" for r in rows),
        "invalid_rows": sum(r["verdict"] == "SKIP" for r in rows),
        "hits": sum(r["verdict"] == "HIT" for r in rows),
        "row_sha256": hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "key_witnesses": [{"fingerprint": fp, "class": key_class[fp],
                           "bits": extracted[fp]["bits"], "witnesses": witnessed[fp]}
                          for fp in sorted(extracted)],
        "source_control_receipt": {
            "positive_plants": sum(x["PASS"] for x in historical["control"]["planted"]),
            "positive_total": len(historical["control"]["planted"]),
            "false_positive_at_10k": sum(x["total"] for k, x in historical["control"]["false_positives"].items() if k.endswith("bar_10k"))},
    }
    assert summary["evaluated_rows"] == 594 and summary["invalid_rows"] == 144 and summary["hits"] == 0
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = replay()
    if args.check:
        assert output == json.loads((HERE / "results.json").read_text())
    else:
        (HERE / "results.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8", newline="\n")
    print({k: output[k] for k in ("all_named_rows", "evaluated_rows", "invalid_rows", "hits")})


if __name__ == "__main__":
    main()
