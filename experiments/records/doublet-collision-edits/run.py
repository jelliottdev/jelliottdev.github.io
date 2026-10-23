"""Fixed collision-edit controls for the LP2 doublet-mechanism proposal."""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ALPHABET = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᛠᛡᚣ"
assert len(ALPHABET) == len(set(ALPHABET)) == 29


def source_pages():
    return [(f"lp2-{i:02d}", ROOT / "text" / f"lp2-{i:02d}.txt") for i in range(56)]


def runes(raw: str) -> str:
    return "".join(char for char in raw if char in ALPHABET)


def doublets(s: str) -> int:
    return sum(a == b for a, b in zip(s, s[1:]))


def transform(s: str, rule: str) -> str:
    if not s:
        return s
    out = [s[0]]
    for previous, current in zip(s, s[1:]):
        if previous == current:
            if rule == "delete_later":
                continue
            if rule == "insert_fixed_f":
                out.append(ALPHABET[0])
            elif rule == "insert_nonmatching":
                out.append(ALPHABET[(ALPHABET.index(current) + 1) % 29])
            else:
                raise ValueError(rule)
        out.append(current)
    return "".join(out)


def toy_ambiguity(rule: str) -> dict:
    by_length = []
    for length in range(1, 6):
        inverse = {}
        for chars in itertools.product(ALPHABET[:3], repeat=length):
            original = "".join(chars)
            inverse.setdefault(transform(original, rule), []).append(original)
        collisions = {output: originals for output, originals in inverse.items() if len(originals) > 1}
        by_length.append({
            "original_length": length,
            "originals": 3 ** length,
            "distinct_outputs": len(inverse),
            "ambiguous_outputs": len(collisions),
            "largest_preimage": max(map(len, inverse.values())),
            "first_collision": next(iter(sorted(({"output": o, "inputs": v} for o, v in collisions.items()), key=lambda x: x["output"])), None),
        })
    return {"alphabet": list(ALPHABET[:3]), "by_length": by_length}


def report() -> dict:
    inputs = []
    pages = []
    for page, path in source_pages():
        raw = path.read_bytes()
        s = runes(raw.decode("utf-8"))
        inputs.append({"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": hashlib.sha256(raw).hexdigest()})
        pages.append((page, s))
    rules = {}
    for rule in ("delete_later", "insert_fixed_f", "insert_nonmatching"):
        per_page = []
        for page, s in pages:
            t = transform(s, rule)
            per_page.append({"page": page, "input_runes": len(s), "input_doublets": doublets(s), "output_runes": len(t), "output_doublets": doublets(t)})
        rules[rule] = {
            "input_runes": sum(x["input_runes"] for x in per_page),
            "input_doublets": sum(x["input_doublets"] for x in per_page),
            "output_runes": sum(x["output_runes"] for x in per_page),
            "output_doublets": sum(x["output_doublets"] for x in per_page),
            "toy_ambiguity": toy_ambiguity(rule),
            "pages": per_page,
        }
    return {"schema": "liberpedia-collision-edit-results-v1", "plan_sha256": hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest(), "inputs": inputs, "rules": rules}


def main() -> None:
    fresh = json.dumps(report(), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    path = HERE / "results.json"
    if "--check" in sys.argv:
        if not path.exists() or path.read_text(encoding="utf-8") != fresh:
            raise SystemExit("collision-edit results differ; run without --check to inspect")
        print("Collision-edit results match")
    else:
        path.write_text(fresh, encoding="utf-8", newline="\n")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
