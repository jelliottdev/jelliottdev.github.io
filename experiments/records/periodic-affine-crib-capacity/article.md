## Result

**A twelve-rune opening becomes easier to fit as a periodic cipher gains free maps—but a fit is not a reading.** We paired each of **nine fixed known-reading openings** with the first twelve runes of each of **55 LP2 pages**, then asked whether a period of 1–8 invertible affine maps could produce it. That is **495 page-and-opening pairs per period**.

| Period | No compatible key | One key | Many keys | Compatible keys when a pair fits |
| --- | ---: | ---: | ---: | --- |
| 1–5 | 495 at each period | 0 | 0 | — |
| 6 | 208 | 276 | 11 | 1–28 |
| 7 | 233 | 0 | 262 | 784–21,952 |
| 8 | 202 | 0 | 293 | 614,656–17,210,368 |

At period 8, a visually promising twelve-rune opening can leave **hundreds of thousands or millions of keys**. The opening alone then has little power to identify an intended mechanism. Conversely, an impossible case rules out only that **specific opening at page position zero under that exact period and affine rule**.

![Counts of impossible, unique-key and many-key fits for each period across 495 fixed page-and-opening pairs.](experiments/records/periodic-affine-crib-capacity/fits.svg)

## Why the key count grows

The model is `Pᵢ = aᵣCᵢ + bᵣ (mod 29)`, where `r = i mod p`, `p` is the period, and each multiplier `aᵣ` is nonzero. Each residue has its own affine map. A single ciphertext/plaintext observation leaves **28** possible maps for that residue. Two distinct ciphertext values paired with distinct plaintext values determine **one** invertible map; contradictory observations leave **none**. We count the choices for each residue and multiply them, without attempting `812^p` full keys one by one.

With twelve proposed runes and period 7, two residues appear only once, leaving at least `28² = 784` keys whenever a fit exists. At period 8, **four** residues appear only once, leaving at least `28⁴ = 614,656`. Repeated ciphertext in another residue can leave an additional factor of 28. This is why raw compatibility becomes less persuasive as the period grows.

We also inspected the **next twelve ciphertext positions** without supplying a proposed continuation. Among compatible pairs, the number of output positions forced to a single rune ranged from **10–12** at period 6, **6–9** at period 7, and **3–6** at period 8. These are conditional predictions; we did not call the predicted runes a decipherment or grade them against invented English text.

## Scope and checks

The [frozen plan](experiments/records/periodic-affine-crib-capacity/plan.json) uses the same nine twelve-rune opening vectors as the earlier [known-key test](#/experiments/lp2-known-vigenere-keys), plus the first 24 archived runes of LP2-00–55 except runeless LP2-50. Headings count; punctuation does not. The [case results](experiments/records/periodic-affine-crib-capacity/results.json) retain every residue's 0, 1 or 28 choices, total compatible keys, and number of forced next positions.

A planted period-3 key on a known 24-rune reading was recovered uniquely, with all twelve following symbols forced. Separately, the counting theorem agreed with literal full-key enumeration in **6,561** small-field cases over F₃, including contradictions and ambiguous keys. Run `python experiments/records/periodic-affine-crib-capacity/run.py --check` and the independent algebraic oracle `python experiments/records/periodic-affine-crib-capacity/check.py` to reproduce the census and controls.

Only nine specified openings at the very start of each page and periods 1–8 were tested. Other plaintext openings, later alignments, clock resets, mixed alphabets, nonlinear transitions and noninvertible rules remain outside this result. The historical Alberti-disk proposal has additional branching rules that are not specified here.
