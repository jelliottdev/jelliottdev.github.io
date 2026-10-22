# Equal-rune pairs at distances one through five

The 86 neighboring equal-rune pairs are unusual under a count-preserving page shuffle. **The same deficit does not continue through lags 2–5** under this particular reference model. This narrows the observation: it concerns adjacency, rather than a blanket avoidance of repeating a rune within five positions.

## Exactly what was compared

For each archived LP2-00–55 page, retain the 29 alphabet runes in order, including headings, and remove other characters. At lag *d*, compare rune *i* with rune *i + d* for every position that fits. Pairs may cross a word or line break after filtering; none cross a page boundary. LP2-50 contributes no rune pairs. A lag is measured in **rune positions**, not in the sequence of extracted doublet events used in the [event-lag experiment](#/experiments/doublet-event-lags).

| Rune lag | Equal pairs | Pairs compared | Page-shuffle expected | Central 95% of 2,000 shuffles |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 86 | 12,901 | 439.17 | 398–480 |
| 2 | 435 | 12,846 | 437.29 | 396–479 |
| 3 | 434 | 12,791 | 435.42 | 396–476 |
| 4 | 451 | 12,736 | 433.55 | 392–472 |
| 5 | 463 | 12,681 | 431.68 | 391–469 |

![Five horizontal rows show observed equal-rune pair counts against the page-shuffle central ranges. Lag one is far left of its range; lags two through five lie within theirs.](experiments/records/doublet-lag-profile/profile.svg)

The dark dot is the observed count, the pale band is the middle 95% of seeded shuffles, and the thin mark is the exact expected count. The band is a visual reference for one shuffle model, not a general confidence interval for possible ciphers. Lag five sits near its upper edge; its 463 matches were met or exceeded in 109 of the 2,000 shuffles. This is not a basis for selecting lag five as a discovery after seeing the chart.

## Why the shuffle expectation changes with lag

For a page with *n* runes and symbol counts *c*, any pair of distinct positions matches with probability `Σ c(c−1) / [n(n−1)]` after uniformly shuffling that page. A lag *d* supplies `max(n−d, 0)` pairs. Multiply and sum over pages to get the exact expected count shown above. The denominator falls as the lag grows; the expectation therefore changes even when the per-pair shuffled probability is the same.

Each of the 2,000 trials independently permutes the filtered runes **within each page**, preserving the page lengths and rune frequencies. It does not simulate English, a running-sum cipher, or a key process. None of those trials had as few as 86 lag-one matches, but `0/2,000` only bounds what this Monte Carlo run observed. The [uniform additive-key record](#/experiments/uniform-additive-doublets) supplies an exact probability for a different, more restrictive model; its tail should not be transferred to this shuffle model.

The observed contrast is compatible with several mechanisms: a rule that avoids immediate repeats, a plaintext/cipher relation that makes adjacent repeats rare, or preprocessing that alters adjacent symbols. It does not identify which one applies. Also, lags 2–5 were selected after the adjacency anomaly was known. The shaded bands are descriptive and unadjusted for multiple looks.

This profile filters out the separators between runes. The [boundary audit](#/experiments/doublet-boundaries) shows that 26 of the 86 adjacent equal-rune pairs have an intervening row wrap or punctuation mark in the archived text.

## Reproduce

Extract the experiment download without flattening folders. Python 3.12 and its standard library suffice:

```text
python experiments/records/doublet-lag-profile/run.py --check
python experiments/records/doublet-lag-profile/check.py
```

The producer records SHA-256 hashes of all 56 page texts and the index. Run `--write` to regenerate the stored JSON and SVG. The second script independently extracts Runic Unicode characters with a regular expression, recounts each lag and derives the exact shuffle expectations. The JSON includes exact fractional expectations, shuffle intervals, counts on either side of each observed result, seed and quantile convention. This is a transcription-based analysis; it does not resolve disputed glyph readings in the source photographs. For the complete 86-event ledger and the algebraic EA proposal, see [the doublet guide](#/wiki/doublets).
