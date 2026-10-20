## What is being tested?

A reported periodic-IoC peak on LP2-54–55 motivates this test. We ask whether a precise ciphertext-autokey model, with selected F runes acting as interruptions, produces an unusually high score after searching all permitted masks and periods.

This is a new bounded implementation. The source discussion names scripts and plots, but their complete files were not supplied. We cannot claim to reproduce their exact processing or graphs.

## Ciphertext feedback, step by step

Represent each rune by its zero-based index in the 29-rune alphabet. F has index zero. Keep a state containing the preceding ciphertext value, initially zero. For an ordinary rune:

```
output = (current ciphertext - previous ciphertext state) mod 29
previous ciphertext state = current ciphertext
```

That is ciphertext feedback: the state receives the input rune, not the decoded output. Plaintext autokey is a different recurrence.

For a selected F interruption, emit F unchanged, set the previous ciphertext state to zero, and exclude that emitted F from the scored stream. Unselected F runes follow the ordinary rule. After removing selected Fs, number the remaining output consecutively from zero for the periodic calculation.

The sibling [skip variant](#/experiments/lp2-54-55-autokey-skip) changes only how the state behaves at a selected interruption. A useful distinction: in reset mode, ordinary adjacent ciphertext differencing already uses F=0 as the next state. Selecting an F therefore removes its own scored output without otherwise changing the following arithmetic. Skip mode instead changes the next non-interruption output by retaining the earlier ciphertext value.

## A small control before the manuscript

In a teaching alphabet modulo ten, encrypt plaintext 1,2,0,3,4 with initial state zero and the third position selected as an interruption:

| Rule | Ciphertext |
| --- | --- |
| Reset state at the selected zero | 1,3,0,3,7 |
| Retain state across the selected zero | 1,3,0,6,0 |

The skip result is 13060, not 13064. Once the next ordinary symbol is processed, the state must update again; carrying an extra lag forward changes the cipher. The checker verifies encryption and decryption in both directions, including leading, adjacent and trailing interruptions.

## Inputs and search bounds

Concatenate archived LP2-54 and LP2-55, including the heading and removing punctuation. There are 232 + 76 = 308 runes. The state does not reset at the page break.

The six F positions in this combined stream are 41, 65, 195, 247, 257 and 273, counted from zero. A mask is a compact way to specify a subset: bit zero selects the first F, bit one the second, and so on. Mask 0 selects none; mask 63 selects all six. Every one of the 64 masks is tested.

For each output, test all periods 2 through 30 inclusive. Period k groups output positions by their remainder modulo k. Pool ordered equal-symbol pairs across those columns, then divide by all ordered within-column pairs:

```
pooled IoC = sum over columns and runes of count * (count - 1)
             / sum over columns of length * (length - 1)
```

This weights columns by their available pairs. It is not an unweighted average of column IoCs. The search has 64 × 29 = 1,856 parameter configurations; that count does not claim independent evidence from every configuration. See [index of coincidence](#/wiki/index-of-coincidence) and [search bounds](#/wiki/search-space).

## Comparison model

Each of 999 trials retains all six F positions and shuffles the other 302 ciphertext values. It preserves the complete rune counts and length but discards the order of non-F symbols. Each trial starts from a fresh copy; the random seed is 330154.

Repeat the entire 64-mask, 29-period search on every shuffled input and retain its maximum. Comparing the observed maximum with these maxima accounts for mask and period selection inside this declared search. It does not account for the earlier exploration that suggested the pages, cipher model or broader analysis choices.

The two modes use the same shuffled inputs. Their results are related comparisons, not independent replications. We report individual upper-tail estimates and Bonferroni-adjusted estimates for the two planned modes. This adjustment does not turn the original discovery into a prospective test.

## Result

| Quantity | Measured result |
| --- | --- |
| Unique winning mask | 0: no selected interruptions |
| Winning period | 13 |
| Largest pooled IoC | 332/6992 = 83/1748, approximately 0.04748284 |
| Null maxima at least as large | 543 of 999 |
| Corrected Monte Carlo estimate | (543 + 1)/1000 = 0.544 |
| Adjusted for the two planned modes | 1.0 |

Neither the individual estimate nor its two-mode adjustment is below the declared 0.05 threshold. A period-13 peak exists descriptively in this processing, but the test finds no evidence that the selected maximum exceeds this conditional shuffle reference. This is not a decryption and does not rule out period 13, ciphertext autokey or different interruption rules generally.

The [period profile CSV](experiments/records/lp2-54-55-autokey-reset/period-profile.csv) records the best mask at each period alongside the no-interruption score. Its chart joins those observed scores for readability; the upper line may switch masks between points. The [complete results](experiments/records/lp2-54-55-autokey-reset/results.json) retain all 1,856 observed ratios, every null maximum and its winning configurations, plus a source-position trace for each observed winning mask.

## Reproduce and audit

Extract this record's ZIP with its directories intact. The skip variant includes shared code under the reset record's directory; do not flatten the folders. No third-party packages, network calls or AI service are required.

```
python experiments/records/lp2-54-55-autokey-reset/run.py --check
python experiments/records/lp2-54-55-autokey-reset/check.py
```

The full rerun reproduces the observed scores, winning traces and all 999 null maxima. The independent checker uses direct ciphertext indexing instead of mutable feedback state, enumerates same-column pairs to audit every observed score, reconstructs the first two complete null searches with frequency counts, verifies winning traces by re-encryption, and audits the saved tail count. Both checks passed; human review remains pending.

To rebuild the chart and CSV:

```
python experiments/records/lp2-54-55-autokey-reset/plot.py experiments/records/lp2-54-55-autokey-reset
```

## Remaining questions

This model conditions on the observed F locations. It does not measure whether those locations themselves are unusual. It also says nothing about a prose-generating model, different interruption symbols, primers, heading omissions, page-local resets, other period ranges or language-scored candidates. Each changed question needs explicit scope and fresh controls. A high score from any such later search must be compared with a reference that repeats that search.
