# What does the 729 ÷ rune-index proposal actually produce?

A [reported approach to LP2-00–02](#/wiki/reported-attempts?section=cross-section-inversion-729) starts from the section's 729 runes. For each rune, it divides 729 by that rune's zero-based Gematria Primus alphabet index, reduces the integer part modulo 29, then moves by the current line number according to the fractional part. The original discussion also allows neighboring letters, rearrangement and removal when interpreting the result.

This audit checks the **arithmetic and input conventions**, not a candidate reading. The 729-rune total is correct: the three archived pages contain 262, 266 and 201 runes. They occupy **33 printed rune rows** (12, 12 and 9); the number 27 is an arithmetic factor of 729, not the count of printed rows in this transcription.

## The posted first word

The first word on [LP2-00](#/reader/lp2-00) is `ᛋᚻᛖᚩᚷᛗᛡᚠ`. Its GP prime values match all eight numbers quoted in the discussion. The first six zero-based indices also match. For the seventh rune, however, the report treats prime **107** as index **28**; it is at index **27** in the same zero-based 29-rune table that puts prime 53 at index 15. The last rune is F at index zero, making `729 ÷ 0` undefined.

![Eight columns compare the worked example's claimed rune indices with the canonical GP indices and literal outputs.](experiments/records/cross-section-index-inversion/first-word-trace.svg)

[Open the first-word diagram at full size](experiments/records/cross-section-index-inversion/first-word-trace.svg). The independent checker verifies the eight indices against a separately generated prime list. The first seven literal outputs, when the posted less-than-half rule includes an exact zero fractional part, are `L O J I C/K H Y`; the eighth has no output. The report's `AE` at position seven comes from its index-28 calculation, not from the archived rune's GP index. This does not identify why the report used 28.

## Complete arithmetic trace

The [plan](experiments/records/cross-section-index-inversion/plan.json) fixes a transparent convention for a full trace: for nonzero index `j`, compute `q = floor(729/j)`, `r = 729 mod j`, and `base = q mod 29`. Move `+line` if `2r > j`, `−line` if `2r < j`, and zero if equal. Both a global line counter and a counter reset on each page are reported. We save the unwrapped candidate index **and** its modulo-29 form because the discussion does not define how out-of-range positions wrap. F remains undefined rather than being silently changed or omitted.

| Check | Result |
| --- | ---: |
| Runes in LP2-00–02 | 729 |
| Printed rune rows | 33 |
| F runes requiring division by zero | 34 |
| Non-F positions with an out-of-range raw index, global line count | 335 of 695 |
| Same, page-reset line count | 124 of 695 |
| Positions where wrapped global and page-reset outputs differ | 396 of 695 |

These last three counts show how much a complete output depends on two conventions the original post does not settle. They are not chance probabilities or language scores. The [complete results](experiments/records/cross-section-index-inversion/results.json) give all 729 source positions, prime values, quotient/remainder pairs, line numbers, raw candidates and wrapped candidates. No words are moved or deleted in that trace.

## Reproduce and scope

From a checkout or the [experiment bundle](downloads/experiments/cross-section-index-inversion.zip), run:

```text
python experiments/records/cross-section-index-inversion/run.py --check
python experiments/records/cross-section-index-inversion/check.py
python experiments/records/cross-section-index-inversion/plot.py --check
```

The producer verifies the three archived transcription hashes. The checker independently walks every rune, generates the first 29 primes, uses exact fractions to verify the threshold and checks both line conventions. The source discussion is identified by hash in the [reported-attempt entry](#/wiki/reported-attempts?section=cross-section-inversion-729); its pasted text is not redistributed.

**The worked first word is not reproduced by one consistent zero-based GP index rule**, and the formula leaves 34 runes without a result. The proposal could be completed by declaring an F rule, one line clock, one wrap rule and one fixed letter choice, but those would be additional hypotheses. A complete decryption claim would then need continuous output, intact punctuation and word order, and a test on text not used to choose the rules. This audit does not exclude every 729-based or geometric approach.
