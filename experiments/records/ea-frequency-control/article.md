# Does EA occur often enough in solved text?

The proposed rule `Cᵢ = Cᵢ₋₁ + Kᵢ(Pᵢ − 28) mod 29`, with every `Kᵢ` nonzero, makes a ciphertext doublet equivalent to a plaintext EA rune at that transition. This is an **exact property of the proposed equation**, not evidence that Liber Primus uses it. A first check is whether its required EA frequency is plausible in text already decoded into Gematria Primus runes.

The site's solved LP1 controls contain **20 EA runes in 2,782 within-page transition positions** (0.719%). Unsolved LP2-00–55 has **86 doublets in 12,901 within-page positions** (0.667%). If the solved LP1 rate were simply carried over, it would correspond to about **92.7 EA positions** at the unsolved length. That is close to 86, but many different ciphers or text-generation rules can produce the same marginal rate.

![The EA rate in solved LP1 and doublet rate in unsolved LP2 shown as two horizontal bars, 0.719 and 0.667 percent.](experiments/records/ea-frequency-control/comparison.svg)

| Source and measurement | Events | Positions | Rate |
| --- | ---: | ---: | ---: |
| Solved LP1-01, 03–16: decoded GP EA | 20 | 2,782 | 0.719% |
| Solved LP2-56–57: decoded GP EA | 0 | 178 | 0% |
| Unsolved LP2-00–55: equal neighboring ciphertext runes | 86 | 12,901 | 0.667% |

The two solved LP2 pages are short; their zero EA count is not a robust estimate for the much longer unsolved portion. The LP1 pages also differ in section and method from that portion. Resampling the 15 solved LP1 pages 10,000 times gives a descriptive range of roughly **54–132 EA positions** when each draw's rate is scaled to 12,901 positions. This shows how the small control set changes with page mix. It is **not** a predictive interval for unknown LP2 plaintext: the pages are section fragments, not independent random samples from a known common language process.

## Why the spelling conversion matters

The known-reading source preserves actual decoded **GP rune indices** alongside their literal Latin labels. In all 17 solved control pages, removing row wraps and greedily taking the longest GP labels **within each printed token** reconstructs the stored index sequence exactly. That is a check on this literal source layer, not a license to parse normalized English the same way.

If all token boundaries are erased first, greedy parsing finds **31 EA labels** across the solved LP1 pages instead of the actual **20 EA runes**. The eleven extras are cross-word `E|A` joins such as `ONE | ALONG` and `STRUGGLE | AND`. The downloaded report lists all eleven. Even inside one ordinary English word, the letters `EA` do not prove the manuscript used the single EA rune: `REACT` could be segmented `R·EA·C·T` or `R·E·A·C·T`. In Gematria Primus, EA has prime value 109, while E plus A totals 67 + 97 = 164. Preserve original rune boundaries when testing a frequency or prime sum.

## What about the difference IoC?

Subtract each within-page ciphertext rune from the next modulo 29. This gives 12,901 differences, including 86 zeros. Their observed index of coincidence is **0.035325**. Under an additional idealized assumption—condition on exactly 86 zero differences, then draw all 12,815 nonzero values independently and uniformly from residues 1–28—the expected IoC is **0.035284**. In 2,000 seeded simulations, the central 95% interval was **0.035249–0.035326**; 54 trials reached or exceeded the observed value.

So 0.0353 is near the upper edge of this **conditional nonzero-uniform** reference, not a standalone confirmation. The reference was chosen after the zero deficit and IoC were known, and other features and baselines have also been examined. Shuffling the ciphertext runes within pages would change the zero count and ask a different question. Uniform nonzero differences are what independently uniform nonzero keys would imply at non-EA positions for this particular equation; other key schedules can behave differently.

The [doublet placement audit](#/experiments/doublet-placement) tests a different implication: whether the 86 candidate EA positions have unusual page counts or short gaps under explicit event-placement controls. Those controls also cannot establish a plaintext reading.

## Reproduce and limits

Extract the experiment ZIP without flattening it. Python 3.12 and its standard library suffice:

```text
python experiments/records/ea-frequency-control/run.py --check
python experiments/records/ea-frequency-control/check.py
```

The producer hashes the known-reading extract, alphabet and all 56 unsolved text files. The independent checker recounts decoded EA indices, reconstructs literal labels, verifies the cross-word joins, and recalculates the exact difference IoC. The source extract uses established decoded readings and a documented LP1-10 correction; this experiment is not a fresh image audit. It cannot tell whether the 86 doublets are plaintext EA, nor recover the nonzero key sequence. See [the doublet guide](#/wiki/doublets?section=ea-constraint) for the equation and its assumptions, and the [boundary audit](#/experiments/doublet-boundaries) for where the 86 pairs sit relative to stored separators.
