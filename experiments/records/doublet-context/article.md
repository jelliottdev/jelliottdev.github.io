# What surrounds the 86 ciphertext doublets?

The [doublet guide](#/wiki/doublets?section=ea-constraint) describes one proposed equation in which a repeated ciphertext rune would mark a plaintext EA. That statement is easy to overread. It fixes the **plaintext symbol at a transition** under the equation; it does not say that the repeated *ciphertext* rune is the EA rune, or that the neighboring ciphertext runes should spell an English word. This experiment records those local ciphertext values and asks whether they have extra ordering structure under a declared conditional control.

![Counts of all 29 ciphertext symbols at the 86 doublet positions, compared with means from fixed-mask within-page permutations.](experiments/records/doublet-context/context.svg)

## What the equation predicts

For `Cᵢ = Cᵢ₋₁ + Kᵢ(Pᵢ − 28) mod 29` with nonzero `Kᵢ`, `Cᵢ = Cᵢ₋₁` if and only if `Pᵢ = 28` (EA). The doublet's visible rune is `Cᵢ`, the **current ciphertext state**. It can be any of the 29 runes. A doublet on AE does not make AE the proposed plaintext; a doublet on EA does not offer special confirmation.

If the *following* plaintext rune is not EA and its key is independently uniform on 1–28, its difference `Cᵢ₊₁ − Cᵢ` is uniform on those 28 nonzero residues. The next ciphertext rune is then uniform over the 28 symbols **other than** `Cᵢ`. It is not independent of `Cᵢ` in absolute symbol terms, because equality is forbidden. If the following plaintext is EA, the next difference is zero and a triple results. The observed doublet mask has no consecutive zeros, so this record cannot use a fixed-mask control to judge how surprising that absence is.

## The actual local inventory

From the archived LP2-00–55 text, filter to the 29 GP runes, keep headings, and compare neighbors only within pages. This gives **86 zero differences in 12,901 transitions**. Each event is recorded by page and zero-based rune index in the [result ledger](experiments/records/doublet-context/results.json). One event has no preceding within-page difference; one has no following one. None has a zero difference immediately beside it. The remaining 85 preceding and 85 following differences are tabulated separately in all 28 nonzero residues.

The event-symbol counts range from **0 to 7**, rather than 3 to 7. GP index 17 (B) has no event; index 25 (AE) has seven; index 28 (EA) has three. The latter labels are ciphertext symbols, not decoded plaintext. Across all 29 bins there are **123 pairs of events sharing the same ciphertext symbol**. The local before-versus-after residue imbalance, defined in the [plan](experiments/records/doublet-context/plan.txt), is **27.786**. Both summaries were selected before this control was run, but the underlying doublet observation had already been seen.

## A control that holds the known anomalies fixed

For each page, retain its first ciphertext rune, the positions of all zero differences and the multiset of all nonzero differences. Shuffle only the nonzero difference order within that page, then cumulatively add the differences modulo 29 to rebuild a synthetic ciphertext page. This preserves the **86-event mask exactly** and also preserves each page's difference histogram. It asks whether *placement relative to those zeros* adds anything beyond those known properties. It does not simulate English, a key generator, or the chance of obtaining 86 zeros in the first place.

| Diagnostic | Observed | Central 95% of 5,000 conditional permutations | Trials at least observed |
| --- | ---: | ---: | ---: |
| Same-symbol pairs among doublet events | 123 | 108–150 | 2,950 / 5,000 |
| Before/after difference imbalance | 27.786 | 12.745–34.259 | 854 / 5,000 |

Both observed values sit inside these conditional ranges. In the figure, blue bars are the complete observed 29-symbol inventory and red ticks are the average count for each bin across the permutations. The ticks are not 29 separate significance cutoffs. The report also includes all 28 before and after residue bins, every event location, the seed (`330122`), and both inclusive rank directions.

This is **not independent corroboration** of the earlier [nonzero-difference histogram](#/experiments/ea-difference-independence). The same source differences are reused, and the new control deliberately fixes their pagewise histograms. The broad question “are these 86 positions really plaintext EA?” remains unanswered. A proposed key schedule would have to predict something further that can be checked without freely choosing plaintext neighbors after seeing the ciphertext.

## Do hyphen-crossing doublets have different neighbors?

The [boundary ledger](#/experiments/doublet-boundaries) classifies **22** doublets as crossing a hyphen, **63** as within a rune token under the site's rule, and **one** as crossing other punctuation. The last event is kept in the [complete companion ledger](experiments/records/doublet-context/boundary-context.json) but excluded from this two-group comparison. Calling all 64 non-hyphen events “within-word” would misclassify that one event; even the 63-token group is a transcription convention, not a fresh image review.

For a repeated ciphertext rune at position `i`, the immediately preceding rune is at `i−2` and the following rune at `i+1`, if those positions exist within the same page. The table counts **ciphertext** GP labels. Circular distance means the smaller of the two distances between their indices around the 29-symbol alphabet; it does not measure English-letter similarity.

| Doublet group | Events | Before available / distinct labels | Mean before distance | After available / distinct labels | Mean after distance |
| --- | ---: | ---: | ---: | ---: | ---: |
| Hyphen-crossing | 22 | 22 / 16 | 5.95 | 22 / 17 | 8.23 |
| Within-token | 63 | 62 / 25 | 8.06 | 62 / 25 | 7.87 |
| Other separator, excluded from comparison | 1 | 1 / 1 | 2.00 | 1 / 1 | 5.00 |

There is a visible difference in the *mean preceding circular distance*, but that summary was inspected after this question arose. For a broader comparison fixed in the [companion plan](experiments/records/doublet-context/boundary-context-plan.json), we sum the two-group Pearson association scores over all 29 before-rune labels and all 29 after-rune labels, retaining a separate category for a missing page-edge neighbor. The observed score is **51.321**. We then keep every observed before/after context vector intact and permute which 22 of the 85 eligible events carry the hyphen label. In **6,495 of 10,000** global shuffles the score is at least this large; the central 95% of shuffled scores is **39.592–71.390**. A second control preserves each page's hyphen count and yields **8,626 of 10,000** at least as large, with a central range of **46.195–75.474**. Only **13 pages and 40 events** have labels that can move in that stricter control.

These are exploratory conditional ranks, not prospective p-values or a test that the 22 marks were placed randomly. The 22-event group is small, many labels are sparse, and page layout can affect both boundary status and ciphertext context. The whole-label statistic does not stand out under either stated comparison; it does not rule out a particular word-boundary cipher rule. In the proposed EA-stalling equation, the runes around a doublet remain ciphertext states. They cannot be compared directly with English words containing EA without a separately fixed key and boundary clock.

## Reproduce and limits

Extract the experiment ZIP without flattening it, then run:

```text
python experiments/records/doublet-context/run.py --check
python experiments/records/doublet-context/check.py
python experiments/records/doublet-context/boundary_context.py --check
```

The producer reruns all 5,000 seeded conditional permutations and checks the saved JSON and SVG byte for byte. The separate checker re-extracts the Runic Unicode block, recomputes all 86 event locations and both diagnostics, and verifies each source hash. The companion script hashes both source ledgers, joins all 86 events by page and rune position, verifies neighboring runes against the archived page text, and reruns both 10,000-draw boundary-label controls. This checks the archived text, not a fresh image transcription. Neither control nor the exact algebra identifies the cipher, and these exploratory ranks are not adjusted for the wider history of questions asked of the same 86 events. See the [boundary audit](#/experiments/doublet-boundaries) and [placement audit](#/experiments/doublet-placement) for other, non-interchangeable scopes.
