"""Check the saved source unigram threshold diagnostic, not LP2 ciphertext."""
import json
import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent


def jsd_fitness(observed, target):
    counts = [0] * 29
    for n in observed:
        counts[n] += 1
    total = len(observed)
    p = [count / total for count in counts]
    jsd = 0.0
    for a, b in zip(p, target):
        mean = (a + b) / 2
        if a:
            jsd += a * math.log(a / mean) / 2
        if b:
            jsd += b * math.log(b / mean) / 2
    return 1 / (1 + jsd)


def main():
    receipt = json.loads((HERE / "source-control.json").read_text(encoding="utf-8"))
    spec = receipt["uniform_control"]
    rng = random.Random(spec["seed"])
    values = [jsd_fitness([rng.randrange(29) for _ in range(spec["runes_per_trial"])], receipt["source_unigram_target"])
              for _ in range(spec["trials"])]
    ordered = sorted(values)
    assert sum(x > spec["threshold"] for x in values) == spec["pass_count"]
    for field, actual in (("min_score", ordered[0]), ("median_score", (ordered[499] + ordered[500]) / 2),
                          ("max_score", ordered[-1])):
        assert abs(actual - spec[field]) < 1e-12, (field, actual, spec[field])
    print("Source unigram diagnostic reproduced: 1,000/1,000 random 262-rune strings exceed 0.85")


if __name__ == "__main__":
    main()
