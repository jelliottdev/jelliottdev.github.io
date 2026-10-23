# What separates LP2’s surviving doublets?

**Finding.** Wulfic's pinned H/O tests find no source-defined concentration of the **86 surviving adjacent equal-rune pairs** by other difference value, written-line break, short period or marked section. Two named key-switch constructions make too few repeats on solved text. A specific “skip to the next key value” model disagrees with LP2's nonzero differences. None of these checks identifies the encryption method.

The blue marks show where each surviving repeat occurs in nine manuscript sections, labeled by the feature used to recognize each part of the book. A section with more runes has a longer bar. The very short number-square section has no repeat; the others do not show a single concentrated pocket.

![Eighty-six equal-rune pairs marked along nine proportional manuscript sections.](experiments/records/wulfic-doublet-leak-h-o/distribution.svg)

Line endings were one proposed place for a special rule. Here, their repeat rate is nearly the same as elsewhere and well below that rule's 2.5% decision line.

![Repeat rates within written lines and across line breaks, with the proposed line-end threshold.](experiments/records/wulfic-doublet-leak-h-o/line-breaks.svg)

The count here is **86 / 12,947 adjacent pairs**. The source joins pages *within* each of nine marked manuscript sections and never compares across a section boundary. Liberpedia's page-only doublet records use **86 / 12,901** instead. The source's **48 page-break pairs** are part of its line-break category; they should not be added again as separate opportunities. Our independent extractor reproduces every one of the source's 12,947 pair records from the site page text and its written-line markers.

| Source check | Result and decision line | What that establishes |
| --- | --- | --- |
| **H1 · Where did missing repeats go?** | Largest departure among 28 nonzero difference bins: **z = −2.58** at residue 17; source line is absolute z of 3.5 | No single nonzero residue shows the source's proposed compensating nudge. |
| **H2 · A rule at line ends?** | **82/12,362** within lines, **4/585** across written-line breaks, **0/48** across page breaks; source line-end rule requires at least 2.5% | The line-break rate, about 0.68%, does not rise to that rule. |
| **H3 · A repeating phase?** | Best of periods 2–32 under two position clocks: **p = 0.0355** at period 27, joined clock; corrected line **0.000161** | No period passes the declared 62-way selection threshold. |
| **H4 · Section clusters?** | Nine-section χ² **5.33** on 8 df, **p = 0.721**; 500-pair window dispersion **1.022**, inside the source's 0.5–2 band | Surviving pairs are not unusually uneven by either specified summary. |
| **H5 · Two-key collision switch?** | On 2,901 solved runes, DIVINITY/CIRCUMFERENCES gives **6/2,900** repeats under the ideal rule and **10/2,898** under the literal code; φ(primes)/primes gives zero under both | Those two named switch constructions, transferred to this solved text, produce too few repeats to match LP2's source rate. |
| **O · Skip-next-key rule?** | LP2's specified 28-bin difference log-likelihood ratio is **−21.34 nats**, below the source's **−10** exclusion line | The stated model, with a 19% key-repeat parameter and solved-text difference distribution, fails its own prediction. |

The source's **16 relevant assertions pass**, including planted controls for the H patterns and three skip-next versus fresh-rekey simulations. The O result also stays below its line when its plaintext-difference distribution is estimated from either of two disjoint solved-text subsets. These controls support the *specific* tests, not every way a cipher might suppress repeated runes. H5's “literal” implementation can leave positions unset; its eligible-pair denominator is therefore smaller and is reported separately.

## Reproduce and limits

The [plan](experiments/records/wulfic-doublet-leak-h-o/plan.json) fixes all source rules and thresholds. [Inputs](experiments/records/wulfic-doublet-leak-h-o/inputs.json) preserve the pair ledger and solved-text control stream; [results](experiments/records/wulfic-doublet-leak-h-o/results.json) contain all 62 period/clock rows and numerical summaries. An independent standard-library checker re-extracts source-defined pairs from the archived page text, recalculates every row, regenerates the two named key-switch streams, and recomputes the skip-next score:

```text
python experiments/records/wulfic-doublet-leak-h-o/check.py
python experiments/records/wulfic-doublet-leak-h-o/plot.py --check
```

For a complete unchanged-source run, use [Wulfic's checkout at the pinned revision](https://github.com/Wulfic/Cicada3301-Liber_Primus/tree/bf89d3d13aad2b8f2c95ab195cf1b092f250775c):

```text
python experiments/records/wulfic-doublet-leak-h-o/replay_source.py --source PATH_TO_CHECKOUT
```

The relevant source is [`tests/test_leak.py`](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tests/test_leak.py) and [`tools/lpcore/leak.py`](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/lpcore/leak.py). The model assumptions matter: H5 tests only two specified key pairs, on solved text rather than unknown LP2 plaintext; O assumes its fixed 19% repeat rate and solved-text difference profile. The period correction covers the declared 62 phase scans, not all earlier ideas considered about doublets. Other transcriptions, boundary rules and multi-layer ciphers remain outside this result.
