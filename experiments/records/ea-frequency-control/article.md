# Does EA occur often enough in solved text?

A proposed running-sum explanation for the rare repeated runes makes a testable prediction: wherever its rule applies, two equal neighboring ciphertext runes would mark an EA rune in the hidden plaintext. This record asks whether EA occurs about as often in known readings as those repeats occur in unsolved LP2. Matching rates would satisfy one necessary condition; it would not recover plaintext or establish the cipher.

The proposed equation is `Cᵢ = Cᵢ₋₁ + Kᵢ(Pᵢ − 28) mod 29`. Here `C` is the ciphertext rune index, `P` the plaintext index, EA has index 28, and each key value `Kᵢ` must be nonzero. Under those conditions, a ciphertext doublet is equivalent to plaintext EA at that transition. This is an **exact property of the proposed equation**, not evidence that Liber Primus uses it.

The site's solved LP1 controls contain **20 EA runes in 2,782 within-page transition positions** (0.719%). Unsolved LP2-00–55 has **86 doublets in 12,901 within-page positions** (0.667%). If the solved LP1 rate were simply carried over, it would correspond to about **92.7 EA positions** at the unsolved length. That is close to 86, but many different ciphers or text-generation rules can produce the same marginal rate.

![The EA rate in solved LP1 and doublet rate in unsolved LP2 shown as two horizontal bars, 0.719 and 0.667 percent.](experiments/records/ea-frequency-control/comparison.svg)

| Source and measurement | Events | Positions | Rate |
| --- | ---: | ---: | ---: |
| Solved LP1-01, 03–16: decoded GP EA | 20 | 2,782 | 0.719% |
| Solved LP2-56–57: decoded GP EA | 0 | 178 | 0% |
| Unsolved LP2-00–55: equal neighboring ciphertext runes | 86 | 12,901 | 0.667% |

As a scale for sampling variation, a 95% **Wilson score interval** for 20/2,782 is **0.466–1.108%** if those positions were independent draws with one fixed EA probability. The observed unsolved rate, 0.667%, lies inside that interval. The same calculation for 86/12,901 gives **0.540–0.822%**. These intervals overlap, but do not establish equal rates or a cipher: adjacent rune positions in prose are dependent, and the LP1 and LP2 sources are not random samples from one common process.

To reproduce the endpoints for either count, set `p = events / positions`, `n = positions`, and `z = 1.9599639845`. The endpoints are `[p + z²/(2n) ± z√(p(1−p)/n + z²/(4n²))] / [1 + z²/n]`. The page-resampling range below addresses a different source of variation. It also remains descriptive, not a probability distribution for unknown plaintext.

The two solved LP2 pages are short; their zero EA count is not a robust estimate for the much longer unsolved portion. The LP1 pages also differ in section and method from that portion. Resampling the 15 solved LP1 pages 10,000 times gives a descriptive range of roughly **54–132 EA positions** when each draw's rate is scaled to 12,901 positions. This shows how the small control set changes with page mix. It is **not** a predictive interval for unknown LP2 plaintext: the pages are section fragments, not independent random samples from a known common language process.

## Why the spelling conversion matters

The known-reading source preserves actual decoded **GP rune indices** alongside their literal Latin labels. In all 17 solved control pages, removing row wraps and greedily taking the longest GP labels **within each printed token** reconstructs the stored index sequence exactly. That is a check on this literal source layer, not a license to parse normalized English the same way.

If all token boundaries are erased first, greedy parsing finds **31 EA labels** across the solved LP1 pages instead of the actual **20 EA runes**. The eleven extras are cross-word `E|A` joins such as `ONE | ALONG` and `STRUGGLE | AND`. The downloaded report lists all eleven. Even inside one ordinary English word, the letters `EA` do not prove the manuscript used the single EA rune: `REACT` could be segmented `R·EA·C·T` or `R·E·A·C·T`. In Gematria Primus, EA has prime value 109, while E plus A totals 67 + 97 = 164. Preserve original rune boundaries when testing a frequency or prime sum.

## What about the difference IoC?

Subtract each within-page ciphertext rune from the next modulo 29. This gives 12,901 differences, including 86 zeros. Their observed index of coincidence is **0.035325**. Under an additional idealized assumption—condition on exactly 86 zero differences, then draw all 12,815 nonzero values independently and uniformly from residues 1–28—the expected IoC is **0.035284**. In 2,000 seeded simulations, the central 95% interval was **0.035249–0.035326**; 54 trials reached or exceeded the observed value.

So 0.0353 is near the upper edge of this **conditional nonzero-uniform** reference: 54 of 2,000 draws were at least as high (2.7%). The observed value is still inside the central 95% simulation range. This is a mild tension with that one extra uniform-key assumption, not a test of the running-sum equation as a whole and not standalone confirmation. The reference was chosen after the zero deficit and IoC were known, and other features and baselines have also been examined. Shuffling the ciphertext runes within pages would change the zero count and ask a different question. Uniform nonzero differences are what independently uniform nonzero keys would imply at non-EA positions for this particular equation; other key schedules can behave differently.

The key layer explains the limitation. Write the observed difference as `Dᵢ = Cᵢ − Cᵢ₋₁`. For each **nonzero** Dᵢ and every one of the **28 non-EA plaintext symbols** Pᵢ, there is exactly one allowed nonzero key, `Kᵢ = Dᵢ(Pᵢ − 28)⁻¹ mod 29`. Thus an unconstrained key per position can fit *any* proposed non-EA plaintext at those positions. Conversely, an independently uniform nonzero key makes Dᵢ uniform on 1–28 regardless of how uneven the non-EA plaintext letter frequencies are. The conditional IoC can challenge that extra independent-uniform-key assumption; it cannot identify plaintext, establish EA at the 86 positions, or test an unspecified deterministic key schedule. **No fixed key schedule has been applied to unsolved LP2 in this record.** Doing so would be a different, stronger experiment with a declared generator and fixed parameters. Simply deleting the 86 zero differences leaves the same 12,815 nonzero values whose histogram is tested in the [companion record](#/experiments/ea-difference-independence). Deleting ciphertext runes instead creates new adjacencies and is a different operation.

Under the archived boundary rule, **22 of the 86 doublets cross a hyphen**. They are legitimate consecutive runes in the filtered stream but are not within-token repeats. If the proposed recurrence resets at word boundaries, those 22 edges no longer fall under its doublet⇔EA identity. If the key continues over boundaries, the identity still applies to the second rune of each edge, with the hyphen ignored by the cipher clock. The [separator audit](#/experiments/doublet-boundaries) lists every such position; the current count cannot decide which clock Cicada used.

All of these comparisons were designed after the low doublet count was known. A confirmatory version would need a key schedule, starting state, boundary/reset rule, rune mapping and success criterion fixed from evidence independent of the test output, then a prediction of untouched ciphertext or a verified plaintext passage. Merely changing an interval method or reserving positions after inspecting this corpus cannot turn the existing rate match into a prospective test.

The [doublet placement audit](#/experiments/doublet-placement) tests a different implication: whether the 86 candidate EA positions have unusual page counts or short gaps under explicit event-placement controls. Those controls also cannot establish a plaintext reading.

The [nonzero-difference companion](#/experiments/ea-difference-independence) keeps the observed zero positions fixed and checks residue balance and adjacent differences. Its 28-bin chi-square is algebraically the same information as the difference IoC reported above, so the two histogram summaries must not be counted as independent evidence.

## Reproduce and limits

Extract the experiment ZIP without flattening it. Python 3.12 and its standard library suffice:

```text
python experiments/records/ea-frequency-control/run.py --check
python experiments/records/ea-frequency-control/check.py
```

The producer hashes the known-reading extract, alphabet and all 56 unsolved text files. The independent checker recounts decoded EA indices, reconstructs literal labels, verifies the cross-word joins, and recalculates the exact difference IoC. The source extract uses established decoded readings and a documented LP1-10 correction; this experiment is not a fresh image audit. It cannot tell whether the 86 doublets are plaintext EA, nor recover the nonzero key sequence. See [the doublet guide](#/wiki/doublets?section=ea-constraint) for the equation and its assumptions, and the [boundary audit](#/experiments/doublet-boundaries) for where the 86 pairs sit relative to stored separators.
