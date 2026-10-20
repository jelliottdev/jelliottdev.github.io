"""Audit an eight-rune proposed crib; this does not implement a Mobius cipher."""
import hashlib
import json
from math import gcd, isqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def report():
    paths = ["data/index.json", "text/lp2-40.txt"]
    inputs = {path: (ROOT/path).read_bytes() for path in paths}
    alphabet = json.loads(inputs[paths[0]])["alphabet"]
    lookup = {a["rune"]: i for i, a in enumerate(alphabet)}
    assert len(lookup) == 29
    text = inputs[paths[1]].decode("utf-8")
    assert not ({c for c in text if "\u16a0" <= c <= "\u16ff"} - set(lookup))
    ciphertext = [lookup[c] for c in text if c in lookup][:8]
    labels = ["F", "O", "R", "E", "U", "E", "R", "Y"]
    indices = {a["latin"]: i for i, a in enumerate(alphabet)}
    plain = [indices[label] for label in labels]
    # One explicit convention matching the supplied numerical intermediate:
    # shift by +18, then Atbash (28-x), leaving only the initial F untouched.
    shifted_atbash = [0] + [(28-(p+18)) % 29 for p in plain[1:]]
    primes = [n for n in range(2, 18)
              if all(n % d for d in range(2, isqrt(n)+1))]
    schedule = [0] + [p-1 for p in primes]
    assert len(schedule) == 8
    intermediate = [(a+b) % 29 for a, b in zip(shifted_atbash, schedule)]
    required = [(c-x) % 29 for c, x in zip(ciphertext, intermediate)]
    assert ciphertext == [0, 9, 19, 26, 6, 23, 25, 8]
    assert shifted_atbash == [0, 7, 6, 21, 9, 21, 6, 13]
    assert intermediate == [0, 8, 8, 25, 15, 2, 18, 0]
    assert required == [0, 1, 11, 1, 20, 21, 7, 8]
    # Independently compute the totients by counting coprime integers.
    assert schedule[1:] == [sum(gcd(k, p) == 1 for k in range(1, p+1)) for p in primes]
    assert [(x+k) % 29 for x, k in zip(intermediate, required)] == ciphertext
    recovered = [0] + [(10-c+k+t) % 29 for c, k, t in
                      zip(ciphertext[1:], required[1:], schedule[1:])]
    assert recovered == plain
    total = sum(alphabet[i]["prime"] for i in plain)
    return {
        "status": "Proposed plaintext; arithmetic reconstruction only. No selector or cipher search.",
        "input_sha256": {p: hashlib.sha256(b).hexdigest() for p, b in inputs.items()},
        "plaintext_labels": labels, "plaintext_indices": plain,
        "ciphertext_indices": ciphertext,
        "convention": "Only initial F is exempt; +18 then Atbash modulo29; phi(p) starts at p=2 after F.",
        "shift_then_atbash": shifted_atbash,
        "prime_minus_one_schedule": schedule,
        "intermediate": intermediate, "required_additive_key_mod29": required,
        "plaintext_prime_sum": total,
        "plaintext_sum_is_prime": total >= 2 and all(total % d for d in range(2, isqrt(total)+1)),
        "unspecified": ["Mobius input sequence and starting index",
                        "Conversion of three-valued outputs to proposed binary states",
                        "Complete fixed state-to-operation table",
                        "State update order, seeds and further interruption handling",
                        "Held-out plaintext criterion and test bounds"],
    }


if __name__ == "__main__":
    print(json.dumps(report(), ensure_ascii=True, indent=2))
