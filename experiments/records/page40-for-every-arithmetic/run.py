"""Audit the fixed arithmetic in a reported LP2-40 FOR EVERY crib."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def is_prime(n):
    return n >= 2 and all(n % d for d in range(2, int(n**0.5) + 1))


def report():
    plan_bytes = (HERE / "plan.json").read_bytes()
    plan = json.loads(plan_bytes)
    for item in plan["inputs"]:
        assert digest((ROOT / item["path"]).read_bytes()) == item["sha256"], item["path"]

    alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    assert len(alphabet) == 29
    by_rune = {item["rune"]: i for i, item in enumerate(alphabet)}
    line = (ROOT / "text/lp2-40.txt").read_text(encoding="utf-8").splitlines()[0]
    first_two_words = line.split("-")[:2]
    assert [len(word) for word in first_two_words] == [3, 5]
    runes = "".join(first_two_words)
    cipher = [by_rune[rune] for rune in runes]
    plain = plan["source_crib_indices"]
    assert cipher == plan["source_ciphertext_indices"]
    assert [alphabet[i]["latin"] for i in plain] == ["F", "O", "R", "E", "U", "E", "R", "Y"]
    assert len(plain) == len(cipher) == 8

    # The source treats the initial F as an unchanged zero placeholder. The
    # following seven are shifted then reflected in the 29-rune alphabet.
    transformed = [0] + [(28 - ((p + 18) % 29)) % 29 for p in plain[1:]]
    assert transformed == plan["source_transformed_indices"]
    first_primes = [item["prime"] for item in alphabet[:8]]
    assert first_primes == [2, 3, 5, 7, 11, 13, 17, 19]
    totient = [0] + [prime - 1 for prime in first_primes[:-1]]
    assert totient == plan["source_totient_stream"]
    intermediate = [(value + step) % 29 for value, step in zip(transformed, totient)]
    assert intermediate == plan["source_intermediate_indices"]
    residual = [(c - mid) % 29 for c, mid in zip(cipher, intermediate)]
    assert [x % 29 for x in plan["source_signed_residuals"]] == residual

    rows = []
    for position, (rune, p, c, shifted, atbash, step, mid, key) in enumerate(
        zip(runes, plain, cipher,
            [None] + [(p + 18) % 29 for p in plain[1:]],
            transformed, totient, intermediate, residual), start=1
    ):
        rows.append({
            "position": position,
            "proposed_plaintext_label": alphabet[p]["latin"],
            "proposed_plaintext_index": p,
            "archived_cipher_rune": rune,
            "archived_cipher_index": c,
            "shifted_index": shifted,
            "atbash_index": atbash,
            "prime_minus_one_step": step,
            "fixed_intermediate_index": mid,
            "fixed_match": mid == c,
            "required_residual_mod_29": key,
            "source_signed_residual": plan["source_signed_residuals"][position-1],
        })

    sums = {}
    for label, span in (("FOR", plain[:3]), ("EVERY", plain[3:]), ("FOR EVERY", plain)):
        total = sum(alphabet[i]["prime"] for i in span)
        sums[label] = {"gp_prime_sum": total, "is_prime": is_prime(total)}
    return {
        "plan_sha256": digest(plan_bytes),
        "source_report_sha256": plan["source_report_sha256"],
        "page": "lp2-40",
        "archived_first_two_word_lengths": [3, 5],
        "fixed_matches_all_eight": sum(row["fixed_match"] for row in rows),
        "fixed_matches_non_f": sum(row["fixed_match"] for row in rows[1:]),
        "non_f_positions": 7,
        "source_signed_residuals_are_congruent": True,
        "gp_sums": sums,
        "rows": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare with saved results.json")
    args = parser.parse_args()
    result = report()
    if args.check:
        assert result == json.loads((HERE / "results.json").read_text(encoding="utf-8"))
        print("PASS: LP2-40 fixed arithmetic and residual trace reproduced")
    else:
        print(json.dumps(result, ensure_ascii=True, indent=2))
