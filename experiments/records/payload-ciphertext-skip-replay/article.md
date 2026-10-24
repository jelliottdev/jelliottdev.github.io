# Number-grid bytes as an encrypted message

None of the 96 full-length results crossed the fixed English-score threshold. The result checks twelve specific keys and the source's conditional-skip decoder; it does not establish that the payload contains no message.

## What was treated as the message

The 256-byte number-grid payload is the message to decode, and one of twelve proposed streams supplies the key. Earlier payload-as-key tests used those bytes to decode manuscript pages; this test runs in the opposite direction.

Each byte is reduced modulo 29 and treated as a rune index. These are two alternative readings of the same grid, not two recovered messages.

| Input reading | Result |
| --- | --- |
| Majority-byte payload, 256 bytes | 48 configurations; no score passes |
| Decimal-preferred payload, 256 bytes | 48 configurations; no score passes |

## What the controls establish

All 144 test outputs cleared the English-score threshold, but only 137 recovered the complete known message.

The known-message tests use two existing readings plus an explicitly synthetic concatenation of them to reach 256 runes. They are not three independent historical passages.

| Known-message result | Count |
| --- | --- |
| Passing English scores | 144 of 144 |
| Complete correct readings | 137 of 144 |

Every correct reading remained among the final candidates. In seven cases, the search put an incorrect reading first.

A high English score can therefore accept an incorrect reading.

## Exact search settings

Each group tests the same twelve source keys, both arithmetic signs and an optional ciphertext alphabet reversal. Every run decodes all 256 runes, starts at key position 0, retains up to 300 beam paths and allows up to 3 conditional skipped key positions per step. The strict final gate is a normalized English score greater than −5.5; there is no short screen or phase selection.

The keys comprise three prime/totient sequences, the repeated LP2-56 digest, a fixed source excerpt of known readings and seven thematic keywords. Exact source constructors supply 356 key symbols. The decoder appends zeros when more key material is required; it does not continue the original sequence indefinitely.

## Control ranking details

Every correct reading was feasible and retained in the final beam. All seven nonexact results are strict cumulative-ranking losses, with no ties or pruned truths. In one case, choosing by normalized score would recover the truth; the other six incorrect outputs also score slightly better after normalization. All 144 checks with the fixed next-source-key wrong key failed the score gate.

## Target result and finite-key check

The best source score was −6.85528881839596, using the majority-byte input, the LP2-56 digest key, sign −1 and alphabet reversal. It fell below −5.5. The separate normalized-score diagnostic inspected all 27,062 retained terminal hypotheses. Its best score was −6.717071296221741 on the decimal-preferred input with the same key and transformations; it also fell below the gate. The historical source winner is preserved separately.

No target retained path reached key position 356. The zero tail was instead exercised by 24 deliberately constructed structural controls, each with a valid path ending at position 435. Original and explicitly padded native beams agreed exactly; 96 allocation checks verified the source behavior around its padding boundary. These arbitrary-message fixtures test padding and admissibility, not English recovery.

The independent audit reconstructed every target beam and its ordered terminal candidates, scores and pointers. There were no exceptions or skipped target cases.

## Limits and reproduction

This is the complete finite grid in source section 1. Other byte transforms, decompression attempts, block comparisons and later probes in that source program remain outside this record. No whole-search null probability was calibrated, and this English score cannot exclude other keys, messages, languages or cipher rules. Reducing bytes modulo 29 also discards byte information; this is a specified rune-reading hypothesis, not a reversible decoding of every original byte value.

The [reproduction instructions](experiments/records/payload-ciphertext-skip-replay/PORTABILITY.md) distinguish the quick saved-results check from the complete isolated replay. Both exact input variants, frozen controls and protocol, full source/result bytes and independent audit code are included.
