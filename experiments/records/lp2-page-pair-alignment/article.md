# One LP2 page as another page’s key

**Question.** If two ciphertext pages are aligned from their first rune and added or subtracted rune by rune, does any output show unusually concentrated symbols?

**Result.** No. The strongest of **2,970** direct page-pair streams has an index of coincidence (IoC) of **0.0446**: subtracting LP2-55 from LP2-29 across their first 76 runes. Yet **235 of 256** shuffled-control searches produced a maximum at least this large (global empirical *p* = **0.918**). This particular page-on-page alignment does not stand out under the declared concentration measure.

![The observed strongest page-pair IoC is lower than the median shuffled maximum.](experiments/records/lp2-page-pair-alignment/global-max.svg)

## What was compared

We took all **55 rune-bearing pages LP2-00–55**, including headings, and paired every two distinct pages. Each pair begins at rune zero and stops when the shorter page runs out; no page key repeats. At each position we computed both **A + B** and **A − B modulo 29**, yielding 1,485 page pairs and 2,970 output streams. Reversing the pages in a subtraction only negates every output symbol, leaving its IoC unchanged, so unordered pairs suffice for this statistic.

The IoC measures how often two positions in a stream contain the same symbol. It does not tell us whether the stream reads as English. We compared the **largest** observed IoC against the largest in each shuffled trial, so selecting the most attractive pair after viewing all 2,970 outputs is accounted for.

Each trial shuffled all 55 pages once and reused those shared shuffled pages across the entire pair grid. The shuffle was restricted to bands delimited by the observed page lengths. That keeps the exact rune counts in every compared prefix unchanged while disrupting alignment. There were **1,226 bands** across the page set, including 310 one-rune bands; nevertheless **87.8% of rune positions changed** on average. The median control maximum was **0.0476** and its 95th percentile was **0.0531**. The observed maximum was below both.

## What this leaves open

This is a bounded structural check inspired by the catalogued “one ciphertext page as another’s key” idea; it is not a replay of a documented earlier attempt. It does not rule out a page-derived key with a different offset, order, reversal, repetition, interruption, arithmetic rule, or decoding layer. Nor does an ordinary IoC alone prove the absence of meaningful text. The previously documented LP2-as-pad test used LP2 data against *external* artifacts; it did not perform this page-on-page alignment.

Run `python experiments/records/lp2-page-pair-alignment/run.py --check` and `python experiments/records/lp2-page-pair-alignment/check.py` from the repository root. The independent check reads the page JSON, verifies all 2,970 observed scores, the 256 shared-shuffle global maxima, the preserved band counts, and a planted shifted-copy control. `results.json` contains every pair/operation score and the full null-max distribution.
