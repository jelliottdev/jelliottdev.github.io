# Do prime-position routes reveal a reading on LP2-03?

This [archived route program](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/solve_p20.py) takes runes at **nonprime zero-based positions**, tries a Caesar shift, then reads that stream in 58 specified ways. The committed file called `page_20` is **LP2-03**, with **217 runes**, not the 646 stated in the program's opening comment. Its nonprime-position stream has 170 runes; the other 47 lie at prime positions.

## Result

The strongest route was an 11-column reading with **six hits** on the program's short list of English trigrams. When we shuffled the same 217 runes and repeated the *entire* split, shift and route search 199 times, **57 searches reached six or more**. This comparison gives no reason to single out the six-hit route as a reading. It is a descriptive control for this search and this spelling convention, not a model of every possible cipher.

![The best route has six trigram hits; 57 of 199 whole-search shuffles reached at least six.](experiments/records/wulfic-p20-prime-position-routes/comparison.svg)

The pinned program reports ten routes because nine are listed regardless of score and the 11-column route passes its `>5` gate. Its final ordering uses the *length of a formatted report string*, not a language score. The source also prints a distinct **prime rune-index-value split** (65/152); that is not the position split tested by these routes.

## Why the shift and routes need care

Every Caesar shift has the same index of coincidence: renaming the 29 symbols does not change their frequency counts. The program chooses shift zero on the first equal maximum; its displayed “best shift” is therefore not independent evidence for a key. Reversal and the complete column, diagonal, keyword and Deor sorts likewise preserve symbol frequencies. Prime-position sampling, fixed-step sampling, Fibonacci positions and padded spirals can change the stream or its length, so they are reported separately.

Before scoring the manuscript, a planted 170-rune message was recovered through the two-column route and passed the source's `>5` trigram gate. The unmodified staged source agreed with our route names and IoC values for every route it retained on that plant. Our independent checker later rebuilt **all 58** manuscript route sequences and digests, including routes below the source's reporting threshold. The predeclared goal of checking *every route against the unmodified source on synthetic inputs* was not fully met: the original program exposes only retained routes, so the source-parity control covered its retained synthetic rows; independent index-map reconstruction covered the rest. This distinction is in the saved receipts.

## Scope and reproduction

The runner uses the pinned Git bytes for `solve_p20.py`, `pages/page_20/runes.txt` and `data/corpora/deor_poem.txt`. It stages the source file unmodified in a temporary folder because its original Deor path differs from the committed path. Run `python experiments/records/wulfic-p20-prime-position-routes/snapshot_inputs.py --source-root PATH --check`, then `gate.py --source-root PATH --check` and `run.py --source-root PATH --check`. Run `python experiments/records/wulfic-p20-prime-position-routes/check.py` for the separate reconstruction.

The test covers those fixed routes on LP2-03 under the source's variable-length rune transliteration and trigram lists. It does not exclude other layouts, transcription choices, languages, or transposition rules. The related [Deor interlocking-stream test](#/experiments/wulfic-deor-interlocking-streams) splits on prime *rune-index values*, a different operation.
