## Finding

**EGALITARIANISM does not fit this fixed word under one fixed alphabet substitution.** Joining `IA` into one GP rune gives 13 runes for a 14-rune slot. Keeping `I A` separate gives 14, but the same ciphertext F at positions 2 and 6 would have to mean G and T. A fixed substitution cannot do both. None of the 812 invertible affine decoders fits the fourteen-rune spelling.

![The same ciphertext F at positions 2 and 6 would require G and T under the proposed spelling.](experiments/records/lp2-43-egalitarianism-compatibility/conflict.svg)

This is a **newly specified compatibility baseline**, not a replay of the 2019 author's cipher. That proposal explicitly did not assume a monoalphabetic cipher. Its transformation remains unspecified, and the original and corrected mapping diagrams have not been inspected. This result therefore does not reject the broader historical idea.

## The word and the spelling

The inferred slot on [LP2-43](#/page/lp2-43) is page-rune interval **[37,51)**, counting from zero and including every recognized GP rune from the top. It comprises the last ten runes of physical line 2 and first four of line 3. Exterior hyphens delimit the word; its internal slash and newline mark a line wrap.

This slot was inferred from the proposal's page/line description and the original page. It is not a recovered diagram annotation. The supplied page text contains 274 recognized GP runes. The public inputs retain the exact page text, alphabet labels and source coordinates so the extraction can be checked independently.

Only these two exact GP encodings were tested:

| Encoding | Rune count | Result |
| --- | --- | --- |
| E G A L I T A R IA N I S M | 13 | Whole-slot length mismatch |
| E G A L I T A R I A N I S M | 14 | Repetition conflict; no bijection or affine fit |

No phonetic aliases, spelling changes, padding, deletions or sliding alignments were allowed. The calculations use alphabet indices 0–28, not prime values.

## What the fixed models establish

A static bijection assigns each ciphertext rune exactly one plaintext rune, and distinct ciphertext runes must receive distinct plaintext runes. The fourteen-rune spelling violates both requirements. Besides the F-to-G/T conflict, ciphertext labels J and S would both need A, while W and B would both need I. All three conflicts are recorded.

The affine check exhausts `P = aC + b (mod 29)`, with `a = 1..28` and `b = 0..28`. Every one of its **812 decoder outcomes**, including all mismatch positions, is saved. There are zero fits. Affine decoders are a subset of static bijections; these are not independent lines of evidence.

No continuation was decoded or ranked because neither baseline fit. Other cipher families, other positions and altered spellings were not tested. A freely chosen per-position key could fit an arbitrary same-length word, but would supply no independent prediction; no such key was fitted here.

## Correctness checks

Before the original target calculation, implementation and synthetic-control hashes were frozen. The public copy preserves that [freeze manifest](experiments/records/lp2-43-egalitarianism-compatibility/source-freeze.json); [input provenance](experiments/records/lp2-43-egalitarianism-compatibility/provenance.json) distinguishes the original calculation from this portable packaging.

Both encodings were planted at offset 37 in synthetic 274-rune contexts. An affine encoder and its specified non-affine output-label swap passed full alphabet and context round trips. All 812 affine encoder keys for each encoding returned their planted inverse: **1,624 planted-key controls**. Deliberate forward-map, inverse-map and length failures were detected.

The independent checker uses equality relations between position pairs, rather than the producer's assignment tables. It also derives affine keys algebraically. On alphabet sizes 2 and 3, lengths 0–4, all **7,722** ordered ciphertext/plaintext pairs agree with exhaustive permutation counts and affine enumeration. The target ledger is independently checked as well.

These are checks of the implementation, not evidence that the proposed word or a particular cipher was intended.

## Relation to existing work

[Simple substitution and page-opening cribs](#/experiments/monoalphabetic-crib-capacity) applies the same kind of equality constraint to nine fixed twelve-rune openings at page starts. This record adds only one interior word and two encodings. [The LP2-39 header crib test](#/experiments/lp2-39-header-cribs) uses the same finite affine keyspace on a different three-rune passage. Neither earlier scope covered this particular word and slot.

## Reproduce

The download is self-contained: Python's standard library, the small public input files, control receipts and complete target ledger. It needs no private queue, transcript, internet connection or original image download. The source image's hash and public location are preserved in provenance.

```text
python experiments/records/lp2-43-egalitarianism-compatibility/run.py --check
python experiments/records/lp2-43-egalitarianism-compatibility/check.py controls
python experiments/records/lp2-43-egalitarianism-compatibility/check.py target
python experiments/records/lp2-43-egalitarianism-compatibility/plot.py --check
```

The [complete target ledger](experiments/records/lp2-43-egalitarianism-compatibility/target-results.json) retains the wrong-length encoding instead of silently discarding it.
