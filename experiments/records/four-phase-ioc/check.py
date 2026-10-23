"""Independent arithmetic and alternate-seed check for the four-phase record."""
from collections import Counter
import json
from pathlib import Path
import random

from run import load

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def collision(seq):
    n = len(seq)
    return 2 * sum(v * (v - 1) // 2 for v in Counter(seq).values()) / (n * (n - 1))


def measure(seq):
    return sum(collision(seq[p::4]) for p in range(4)) / 4


def main():
    plan, pages, warning = load()
    saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    all_runes = [v for page in pages for v in page]
    assert len(all_runes) == 12956
    assert not any("\u16a0" <= c <= "\u16ff" for c in (ROOT / "text/lp2-50.txt").read_text(encoding="utf-8"))
    assert len(pages[-1]) == 76  # LP2-55 is included after the non-rune page.
    assert len(warning) == 184
    for p in range(4):
        assert abs(collision(all_runes[p::4]) - saved["observed"]["phase_ioc"][p]) < 1e-15
    assert abs(measure(all_runes) - saved["observed"]["mean_phase_ioc"]) < 1e-15

    rng = random.Random(17331)
    hits = 0
    draws = 499
    for _ in range(draws):
        shuffled = []
        for page in pages:
            order = list(range(len(page)))
            rng.shuffle(order)
            shuffled.extend(page[i] for i in order)
        hits += measure(shuffled) >= saved["observed"]["mean_phase_ioc"]
    result = {
        "schema": "liberpedia-four-phase-ioc-check-v1",
        "alternate_seed": 17331,
        "alternate_draws": draws,
        "alternate_mean_tail_hits": hits,
        "alternate_mean_upper_p": (hits + 1) / (draws + 1),
        "source_scope": "LP2-00–55 except LP2-50; 55 rune-bearing pages, 12956 runes"
    }
    if not 0.1 <= result["alternate_mean_upper_p"] <= 0.3:
        raise AssertionError("Alternate-stream estimate diverged from original null check")
    target = HERE / "check.json"
    if target.exists():
        assert json.loads(target.read_text(encoding="utf-8")) == result
    else:
        target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print("PASS: independent IoC arithmetic, original page mapping and second-seed page shuffle")


if __name__ == "__main__":
    main()
