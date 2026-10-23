"""Independent index-permutation check of the rail counts and planted inverse."""
import json
from pathlib import Path

from run import ROOT, HERE, PAGES, page_units, score


def independent_decrypt(values, rails):
    n = len(values)
    order = sorted(range(n), key=lambda i: (min(i % (2 * rails - 2), (2 * rails - 2) - i % (2 * rails - 2)), i))
    out = [None] * n
    for offset, original_position in enumerate(order):
        out[original_position] = values[offset]
    return out


def main():
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
    alphabet = {row["rune"]: row["index"] for row in index["alphabet"]}
    letters = [row["latin"] for row in sorted(index["alphabet"], key=lambda row: row["index"])]
    lexicon = set((HERE / "lexicon.txt").read_text(encoding="ascii").splitlines())
    assert len(lexicon) == result["lexicon_size"]
    pages = [page_units((ROOT / f"text/{page}.txt").read_text(encoding="utf-8"), alphabet) for page in PAGES]
    assert sum(map(lambda x: len(x[0]), pages)) == result["runes"]
    assert sum(len(x[1]) for x in pages) == result["visible_word_slots"]
    counts = {str(rails): sum(score(independent_decrypt(values, rails), lengths, letters, lexicon)
                              for values, lengths in pages) for rails in range(2, 11)}
    assert counts == result["rail_hits"]
    assert sum(score(values, lengths, letters, lexicon) for values, lengths in pages) == result["direct_hits"]
    assert result["controls_at_least_observed"] == sum(x >= max(counts.values()) for x in result["control_best_hits"])
    print("rail-fence-visible-words: independent permutation and scoring checked")


if __name__ == "__main__":
    main()
