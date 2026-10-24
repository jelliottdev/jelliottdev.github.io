## Finding

The relation **c′ = 24 − 2c (mod 29)** appears **77 times in 1,267 eligible pairs**, compared with **44.8 expected** when runes are shuffled within each word. It ranks first among 841 affine maps at lag six; only **3 of 2,000 shuffles** reached 77 matches after choosing their best map.

## What six places apart means

The fourth word on [LP2-02, line 1](#/page/lp2-02?line=1) is `ᛒᛇᛚᛞᚻᛒᛗ`. Its alphabet indices are **17, 12, 20, 23, 8, 17, 19**. Compare positions **1 and 7**: six steps apart, with five runes between them.

The rule gives **24 − 2 × 17 = −10**. Adding 29 gives **19**, the seventh rune’s index. This calculation uses alphabet indices **0–28**; prime values aren’t used. This is one matching pair, not proof of a cipher. The full count is compared with shuffled words below.

![Observed lag-six count compared with fixed-map and best-of-841 word-shuffle means.](experiments/records/word-internal-affine-lags/comparison.svg)

This is a reproducible pattern in the archived transcription. It is **not a recovered encryption rule**. The formula and lag were supplied after exploration; the 841-map comparison does not account for trying other lags, word rules, page subsets, or formula families. The simple 1-in-29 reference would predict 43.7 matches, but it ignores each word's rune composition, so the within-word shuffle is the more relevant comparison here.

## What counts as a word

We split at printed hyphens and full stops, join text across slashes and line breaks, and never connect different pages. This follows the archived transcription's visible separators; it does not settle disputed breaks in the source images. Splitting at **every** non-rune character instead leaves 965 opportunities and 58 matches. That choice would incorrectly turn layout wraps into word breaks. A later [page-join comparison](#/experiments/lp2-page-join-lag-six-sensitivity) recovers **80 matches in 1,290 pairs** by joining rune-to-rune page edges, rather than forcing a break at every page. That explains the supplied count of 80 under one explicit parsing rule. The expected count of 45.7 and its significance were not checked in that comparison; the shuffle results here still apply only to the separated-page rule.

At the same six-rune distance, **389 of 11,359** pairs *crossing* a word gap also satisfy the formula. Thus “zero across word gaps” is false if it means all lag-six pairs whose ends lie in different words. A more specific boundary test would need its own definition.

## What the comparison does and does not show

The formula's count is elevated relative to a fixed-map word shuffle, and it remains unusual against the **best of 841 maps at this one lag**. The report also records the same formula at lags 1–12 and counts on each page, so readers can check whether a few long words or pages dominate it. These are exploratory diagnostics; they do not establish that preventing doublets *causes* the lag-six relation. A causal proposal needs a fully specified generator that predicts both the missing adjacent repeats and the excess lag-six pairs, plus a held-out test.

For the adjacent-repeat baseline, see [equal rune pairs at lags one through five](#/experiments/doublet-lag-profile) and [doublet placement](#/experiments/doublet-placement). Those records measure different events and cannot by themselves confirm the proposed link.

## Reproduce

With Python 3.12 and no extra packages, from the repository root:

```text
python experiments/records/word-internal-affine-lags/run.py --check
python experiments/records/word-internal-affine-lags/check.py
```

The first command rebuilds every count, the 2,000 seeded shuffles, and the figure in memory, then compares them with the saved outputs. The second independently scans the transcription to verify the 77 internal and 389 crossing-gap matches. The [machine-readable result](experiments/records/word-internal-affine-lags/results.json) includes page counts, all lag counts, selection-control ranks, and input hashes.
