#!/usr/bin/env python3
"""Replay the frozen LP2-56 artifact hash matrix. Python standard library only."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VECTORS = {
    "sha512": "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f",
    "sha3_512": "b751850b1a57168a5693cd924b6b096e08f621827444f70d884f5d0240d2712e10e116e9192af3c91a7ec57647e3934057340b4cf408d5a56592f8274eec53f0",
    "blake2b_512": "ba80a53f981c4d0d6a2797b69f12f6e94c212f14685ac4b74b12bb6fdbffa2d17d87c5392aab792dc252d5de4533cc9518d38aa8dbf1925ab92386edd4009923",
}


def digest(algorithm, data):
    if algorithm == "blake2b_512":
        return hashlib.blake2b(data, digest_size=64).hexdigest()
    return getattr(hashlib, algorithm)(data).hexdigest()


def text_bytes(value, variant):
    if variant == "crlf":
        value = value.replace("\n", "\r\n")
    elif variant == "drop-final-lf":
        value = value[:-1] if value.endswith("\n") else value
    elif variant == "one-final-lf":
        value = value.rstrip("\r\n") + "\n"
    elif variant != "exact":
        raise ValueError(variant)
    return value.encode("utf-8")


def build():
    plan_bytes = (HERE / "plan.json").read_bytes()
    plan = json.loads(plan_bytes)
    assert plan["schema"] == "liberpedia-lp2-56-artifact-hash-plan-v1"
    target = plan["target"]["hex"]
    assert len(target) == 128 and len(bytes.fromhex(target)) == 64
    assert list(plan["algorithms"]) == list(VECTORS)
    assert all(digest(alg, b"abc") == expected for alg, expected in VECTORS.items())
    for p in plan["pages"]:
        for kind in ("page", "image"):
            entry = p[kind]
            raw = (ROOT / entry["path"]).read_bytes()
            assert len(raw) == entry["size"] and hashlib.sha256(raw).hexdigest() == entry["sha256"]
    payload_entry = plan["payload"]
    payload = (ROOT / payload_entry["path"]).read_bytes()
    assert len(payload) == 256 == payload_entry["size"]
    assert hashlib.sha256(payload).hexdigest() == payload_entry["sha256"]

    page_data = {p["id"]: json.loads((ROOT / p["page"]["path"]).read_text(encoding="utf-8")) for p in plan["pages"]}
    inputs = []
    for p in plan["pages"]:
        inputs.append(("image-original", p["id"], "exact", (ROOT / p["image"]["path"]).read_bytes()))
    for p in plan["pages"]:
        for variant in plan["text_variants"]:
            inputs.append(("page-raw", p["id"], variant["id"], text_bytes(page_data[p["id"]]["raw"], variant["id"])))
    for section in plan["sections"]:
        literal = "".join(page_data[pid]["reading"]["literal"] for pid in section["pages"])
        for variant in plan["text_variants"]:
            inputs.append(("section-literal", section["id"], variant["id"], text_bytes(literal, variant["id"])))
    inputs.append(("grid-payload", "resolved-256", "exact", payload))
    assert len(inputs) == 412

    rows = []
    for family, candidate, variant, data in inputs:
        for algorithm in plan["algorithms"]:
            value = digest(algorithm, data)
            rows.append({"family": family, "candidate": candidate, "variant": variant,
                         "algorithm": algorithm, "bytes": len(data),
                         "input_sha256": hashlib.sha256(data).hexdigest(),
                         "digest": value, "match": value == target})
    assert len(rows) == 1236
    counts = Counter(row["family"] for row in rows)
    summary = {"schema": "liberpedia-lp2-56-artifact-hash-results-v1",
               "plan_sha256": hashlib.sha256(plan_bytes).hexdigest(),
               "target": target, "target_bytes": 64,
               "input_variants": len(inputs),
               "unique_input_sha256": len({hashlib.sha256(data).hexdigest() for _, _, _, data in inputs}),
               "digest_comparisons": len(rows),
               "family_comparisons": dict(sorted(counts.items())),
               "algorithm_comparisons": {alg: sum(r["algorithm"] == alg for r in rows) for alg in plan["algorithms"]},
               "matches": [r for r in rows if r["match"]],
               "excluded_algorithms": plan["excluded_algorithms"]}
    return rows, summary


def main():
    rows, summary = build()
    with (HERE / "cases.jsonl").open("w", encoding="utf-8", newline="\n") as out:
        for row in rows:
            out.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    (HERE / "results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{summary['digest_comparisons']} comparisons; {len(summary['matches'])} matches; {summary['unique_input_sha256']} distinct input byte strings")


if __name__ == "__main__":
    main()
