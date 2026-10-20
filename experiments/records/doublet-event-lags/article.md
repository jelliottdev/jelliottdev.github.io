# Distances between doublet events

The proposal asks whether repeated runes, extracted in manuscript order, form a patterned sequence of their own. This recount finds **10 forward +4 differences at lag three, out of 83 comparisons (12.05%)**. It does not reproduce the reported 12.9%, and it does not verify the proposed p-value.

“Not supported” refers to reproducing the exact numerical claims with these inputs and rules. It does not mean that every doublet-based cipher has been tested or rejected.

## What is an event?

Read LP2-00–55 in numerical order, including headings. Retain only the 29 alphabet runes within each page. Count overlapping adjacent equal pairs: AAA contributes two A events. Never create an event across a page boundary. Then join the extracted events in page order. The result is 86 events.

At lag one, compare each event with the next; at lag three, compare it with the event three places later. For example, in an event sequence A, B, C, D, the first lag-three comparison is A to D. This lag measures **event positions**, not rune positions or page distance.

For indices a and b, the directed difference is `(b-a) mod 29`. The circular distance is the smaller of that difference and its reverse. Thus +4 and −4 share circular distance 4 but occupy different directed bins, 4 and 25. The proposed +4 claim is directional.

## Complete comparison

| Event lag | Comparisons | Cross-page comparisons | Mean circular distance | Forward +4 | Circular distances 5, 12 or 14 |
| --- | --- | --- | --- | --- | --- |
| 1 | 85 | 41 | 734/85 ≈ 8.6353 | 2 | 31 |
| 2 | 84 | 63 | 52/7 ≈ 7.4286 | 1 | 22 |
| 3 | 83 | 75 | 626/83 ≈ 7.5422 | 10 | 14 |

The earlier proposed lag-one mean was 8.81. These inputs instead give 8.6353. The exact reason for the difference cannot be determined without the original event list and counting implementation. The stored output includes all events and every comparison so a future comparison can locate the first divergence.

Page boundaries matter here: 75 of 83 lag-three comparisons cross them. Resetting the comparisons at page boundaries would answer a different question; it is not an interchangeable implementation detail.

## What should the +4 baseline be?

Under a uniform shuffle of this fixed event multiset, the exact probability of a forward +4 difference between distinct positions is **8/215 ≈ 3.7209%**. It is not exactly 1/29, because these event symbols have unequal frequencies. For counts c(a), sum `c(a) × c((a+4) mod 29)` over all a and divide by `86 × 85`.

This probability is an expectation for a single ordered comparison. Multiplying it by 83 gives the expected lag-three count, approximately 3.0884. It is **not** the probability of observing ten or more matches: comparisons share events, and a binomial independence assumption is not justified by this calculation.

No permutation tail probability is calculated here. Selecting +4, lag three, or the group of distances 5, 12 and 14 after inspecting data introduces selection choices. A later significance test must state which choices it addresses. See [null models](#/wiki/null-models) and [search space](#/wiki/search-space).

## Reproduce and inspect

Extract the experiment ZIP with its folders intact. No packages, network access or AI service are required.

```text
python experiments/records/doublet-event-lags/run.py --check
python experiments/records/doublet-event-lags/check.py
```

The producer uses the included doublet extractor and prints fresh JSON without `--check`. The independent checker uses overlapping regular-expression matches on the archived rune text, then checks every event, lag pair, histogram, distance and boundary flag. It also computes shuffle expectations from symbol frequencies instead of enumerating pairs of event positions.

These checks establish agreement about the archived transcription. They do not independently settle ambiguous handwriting. The [doublet guide](#/wiki/doublets) explains the source rules and supplies the original pair coordinates.
