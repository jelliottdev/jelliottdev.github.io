# Prime-indexed-prime and P.S. keys under a corrected score

An [archived structural-analysis script](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/structural_analysis.py) tries a stream of **prime-indexed primes** and three numerical encodings of its **P.S. number** as rune keys. Its original hit rule requires a raw coincidence score above **1.3**, although that score cannot exceed **1**. The source's absence of hits therefore says nothing about its keys. We tested a clearly labeled amendment: multiply that score by **29** before applying the source's 1.3 screen, leaving its called key generators, page range, offsets, three directions and one-rune-word check intact.

![The impossible source score gate, corrected maximum, and whole-search shuffle comparison.](experiments/records/wulfic-structural-pip-ps-normalized/comparison.svg)

**The corrected search has no screen hit.** Its highest score is **1.226** on LP2-14, below 1.3. In **157 of 199** page-shuffled whole searches, the best score was at least as high as the manuscript maximum; **27** shuffled searches even crossed 1.3. That comparison includes the same choice across pages, keys, offsets and directions. It is a selection control, not a cipher model; neither a low score nor a threshold crossing would itself identify a reading.

## What was searched

The source's `page_21` through `page_54` now correspond to **LP2-04 through LP2-37**. Their flat rune sequences and source-style word boundaries match the pinned source files. The search covers **102,036 settings**: 34 pages × 1,000 prime-indexed-prime offsets × three directions, plus 36 eligible P.S. **decimal-digit** settings. The source's digit-pair and base-29 keys have 66 and 90 symbols; every target page is at least 121 runes long, so neither has an eligible source-defined offset. We did not pad or repeat them. The source prints a partial 7×7 square but never searches it; it is outside this record.

For each setting we apply subtraction, addition or Beaufort decoding modulo 29. Before scoring, every visible one-rune word must decode to the GP indices for **I** or **A**. Only **3,031** of the 102,036 settings pass that filter on the actual pages; all are from the prime stream. The score is `29 × Σ f(f−1) / [n(n−1)]`, where `f` counts each decoded rune and `n` is the page's rune count. The highest-scoring page, LP2-14, has **no one-rune words**, so its 3,000 prime-stream settings all pass that particular filter. No P.S. candidate passes it on the two eligible pages.

The [frozen plan](experiments/records/wulfic-structural-pip-ps-normalized/plan.json) fixes this amended rule and 199 full-search shuffles before the manuscript scan. The [input audit](experiments/records/wulfic-structural-pip-ps-normalized/input-audit.json) records source and local hashes and exact word lengths for all 34 pages. A [source parity check](experiments/records/wulfic-structural-pip-ps-normalized/source-parity.json) compared the GP map, million-limit prime sieve, four derived key streams, decode directions, singleton rule and coincidence arithmetic with the exact pinned program. Twelve planted cases—each key stream in all three directions—recover complete known text and clear the amended screen. These controls show that the corrected screen can report a genuine keyed message; they do not validate an LP2 reading.

## Reproduce

From the checkout or [experiment ZIP](downloads/experiments/wulfic-structural-pip-ps-normalized.zip), run from its root:

```text
python experiments/records/wulfic-structural-pip-ps-normalized/run.py --gate --check
python experiments/records/wulfic-structural-pip-ps-normalized/run.py --run --check
python experiments/records/wulfic-structural-pip-ps-normalized/check.py
python experiments/records/wulfic-structural-pip-ps-normalized/plot.py --check
```

The [results](experiments/records/wulfic-structural-pip-ps-normalized/results.json) retain the page maxima and every shuffle maximum; the independent checker reruns the full source-defined grid and all 199 controls with a separate sieve and scorer. To repeat the optional direct source-function comparison, download the exact pinned source file linked above and run `python experiments/records/wulfic-structural-pip-ps-normalized/source_parity.py --source PATH --check` from the bundle root. The original raw-score gate remains impossible; this result belongs only to the explicitly corrected variant and the source's finite inputs.
