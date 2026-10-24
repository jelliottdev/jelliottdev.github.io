## What the saved outputs already settle

The original known-key search saved every full candidate. For one fixed setting—second-koan key, phase zero, subtraction—we can reuse those outputs to settle most of a proposed reset variant. No new word-reset or line-reset manuscript output was decoded in this audit.

| Reset rule | Pages excluded by an earlier mismatch | Pages still requiring the new test |
| --- | ---: | --- |
| Every transcription word | 54 of 55 | LP2-54 |
| Every CR/LF line boundary | 55 of 55 | None |

![Why only LP2-54 survives the word-reset gate](experiments/records/known-key-reset-prefix-gate/figure.svg)

## Why the gate works

Before the first reset, the new rule consumes exactly the same key values as the saved uninterrupted rule: output index P[j] = (C[j] − K[j mod 13]) mod29. A reset after rune offset b can first affect rune b. Any already incorrect opening rune with zero-based position j &lt; b therefore stays incorrect. Later changes cannot repair it. If no boundary exists, the rules remain identical throughout.

The boundary is a first **possible** change, not a claim that every reset necessarily changes a key value. Leading separators do not change a phase-zero start. Any non-rune ends a transcription word; only CR or LF ends a line for this test. A slash alone does not reset the line clock. These are transcription conventions, not recovered plaintext word boundaries.

## The remaining page

LP2-54's saved output begins [24,9]; Warning begins [24,7]. Its first word boundary follows one rune, exactly where the first mismatch occurs. The strict-before proof cannot exclude this page: its second rune could change. The first line boundary follows 19 runes, so the same page is excluded for line resets. Remaining eligible is not a successful decode.

## Inputs and controls

Both implementations verified every selected saved full output directly against canonical raw pages and the pinned 13-index key: 55 nonempty arrays, 12,956 runes. The archived text files and data/pages raw fields match exactly. The empty LP2-50 array was checked and kept out of the gate denominator. The Warning12 vector was also checked against its saved reading trace.

Four short synthetic controls cover both rules. In each positive control, inverse encoding plants the Warning beginning with a boundary between its first two runes: the uninterrupted mismatch occurs exactly at that boundary, remains eligible, and the reset decoder recovers the planted opening. Changing the first ciphertext rune makes a mismatch before the boundary; the gate rejects it. The independent checker uses positional equations rather than the runner's boundary loop.

## Scope and provenance

This is a post-target audit of [the existing known-key search](#/experiments/lp2-known-vigenere-keys), not a new historical replay or a prospective null experiment. The 54/55 exclusion counts were supplied before this formal audit and then independently recomputed. No parameters, opening vectors or boundaries changed after the audit results. The original nine-opening search remains distinct from this one-opening proof.

## Reproduce

Run `python experiments/records/known-key-reset-prefix-gate/run.py --check` and `python experiments/records/known-key-reset-prefix-gate/check.py` from the repository or extracted bundle root. Both use only Python's standard library and pinned local files. The first reconstructs the gate report; the second independently checks all saved arrays, strict boundary decisions and synthetic controls. Neither runs reset variants on manuscript targets. Machine-readable evidence is in [results.json](experiments/records/known-key-reset-prefix-gate/results.json).
