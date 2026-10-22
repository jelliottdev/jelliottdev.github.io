"""Enumerate two fixed one-step feedback rules on LP2-54; standard library only."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def read_plan():
    return json.loads((HERE / "plan.json").read_text(encoding="utf-8"))


def stream(plan):
    entry = plan["input"]
    raw_bytes = (ROOT / entry["path"]).read_bytes()
    assert hashlib.sha256(raw_bytes).hexdigest() == entry["sha256"]
    raw = raw_bytes.decode("utf-8")
    assert raw.startswith(plan["header_source_prefix"])
    alphabet = plan["alphabet"]
    assert len(alphabet) == len(set(alphabet)) == len(plan["labels"]) == 29
    out = [alphabet.index(ch) for ch in raw if ch in alphabet]
    assert len(out) == 232
    assert [alphabet.index(ch) for ch in raw[:len(plan["header_source_prefix"])] if ch in alphabet] == out[:9]
    return out


def decipher(cipher, primer, mode):
    result = []
    for i, symbol in enumerate(cipher):
        previous = primer if i == 0 else (cipher[i - 1] if mode == "ciphertext_feedback" else result[-1])
        result.append((symbol - previous) % 29)
    return result


def encipher(plain, primer, mode):
    result = []
    for i, symbol in enumerate(plain):
        previous = primer if i == 0 else (result[-1] if mode == "ciphertext_feedback" else plain[i - 1])
        result.append((symbol + previous) % 29)
    return result


def build():
    plan = read_plan()
    cipher = stream(plan)
    alphabet = plan["alphabet"]
    labels = plan["labels"]
    first_candidates = {label: labels.index(label) for label in plan["first_plain_rune_candidates"]}
    cases = []
    for mode in plan["modes"]:
        for primer in range(plan["primer_range"][0], plan["primer_range"][1] + 1):
            plain = decipher(cipher, primer, mode)
            assert encipher(plain, primer, mode) == cipher
            selected = next((label for label, value in first_candidates.items() if value == plain[0]), None)
            cases.append({
                "mode": mode, "primer": primer, "first_plain_rune": selected,
                "header_indices": plain[:plan["header_rune_count"]],
                "header_labels": [labels[x] for x in plain[:plan["header_rune_count"]]],
                "plain_indices": plain,
                "plain_runes": "".join(alphabet[x] for x in plain),
            })
    selected = [case for case in cases if case["first_plain_rune"]]
    assert len(cases) == 58 and len(selected) == 6
    return {
        "schema": plan["schema"], "cipher_runes": "".join(alphabet[x] for x in cipher),
        "cipher_indices": cipher, "header_cipher_indices": cipher[:9],
        "case_count": len(cases), "highlighted_count": len(selected), "cases": cases,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = json.dumps(build(), ensure_ascii=False, indent=2) + "\n"
    target = HERE / "results.json"
    if args.check:
        assert target.read_text(encoding="utf-8") == output
        print("PASS: all 58 feedback cases and their full 232-rune outputs match saved results")
    else:
        target.write_text(output, encoding="utf-8", newline="\n")
        print("Wrote", target)


if __name__ == "__main__":
    main()
