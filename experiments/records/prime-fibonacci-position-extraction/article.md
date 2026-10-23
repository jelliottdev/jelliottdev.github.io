# Runes at prime and Fibonacci positions

**Question.** If the manuscript's rune positions act as an index, does reading only prime- or Fibonacci-numbered runes reveal English text?

**Result.** The tested extractions did not stand out. The strongest score was from taking prime-numbered runes **afresh on every page**, then pooling the evidence across pages. Its score was **−7.472**. In **201 of 256** shuffled-page trials, the strongest of the same tested methods scored at least as well (global add-one estimate **202/257 ≈ 0.786**). The extracted text does not form a readable passage.

![Prime and Fibonacci extraction scores compared with page-preserving shuffled controls.](experiments/records/prime-fibonacci-position-extraction/selection-scores.svg)

## What we selected

There are **12,956** recorded GP runes on the 55 rune-bearing pages LP2-00–55. Position **1** means the first rune, without advancing for punctuation or page artwork. Prime positions start **2, 3, 5, 7**; unique Fibonacci positions start **1, 2, 3, 5, 8**. We tried each selector twice: restarting at every page, and applying it once after joining the pages in numerical order. This is a fixed four-arm test, not an every-*n* or adjustable-start search.

For page-by-page selection, we scored each page's extracted runes separately and combined the quadgram sums. No four-letter group was allowed to cross a page boundary. Joined selection was scored as one stream. Three arms supplied at least the **100 Latin quadgrams** declared for scoring: page-local primes (2,797 selected runes), joined primes (1,542), and page-local Fibonacci (634). Book-wide Fibonacci selected only **20 runes**, yielding 20 quadgrams, so its score was withheld. Its exact stream remains in `results.json`; this short sample cannot support a negative language finding.

Every control trial shuffled the rune order **inside each complete page once**, keeping each page's rune counts. All four selectors then used those same shuffled pages. We compared the best eligible observed arm with the best eligible arm in each trial, accounting for choosing the most attractive of the three scored variants. The page-local prime score was only **0.025** above its own shuffled median; the other two scored arms were about **0.057 below** theirs. A planted known-reading stream at the selected positions was recovered exactly and scored well above each eligible arm's shuffled median, checking that the extraction and scorer can respond to a real GP-encoded passage.

The outcome is bounded. It tests direct English-like readings at these **one-based, forward** positions under two page-boundary conventions. It does not rule out a second cipher layer, different starting positions, backwards reading, an indexed key rather than direct text, another language, or other ways of treating page divisions. The source catalog lists the idea; it is not evidence that a particular historical attempt used these exact rules.

Run `python experiments/records/prime-fibonacci-position-extraction/run.py --check` and `python experiments/records/prime-fibonacci-position-extraction/check.py` from the repository root. Both use Python 3's standard library. The independent check reconstructs pages from the page JSON, computes positions by a separate algorithm, and verifies all 256 shared-control scores. `results.json` preserves every extracted segment, its GP indices and Latin labels, so the precise reading can be inspected without recomputing it.
