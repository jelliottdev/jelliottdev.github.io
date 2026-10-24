# Autokey with skipped key positions

No candidate crossed this search's English-score threshold. But the check does not rule out autokey: in 247 of 360 known-message tests, the source encoder and decoder follow different rules.

The complete source grid tested 45 starting keys, two feedback sources and both arithmetic directions on 55 nonempty manuscript segments: 9,900 full-page decodes. None scored above the fixed −5.5 gate. A separate check of every retained terminal path also found no crossing.

## Two ways to continue the key

An autokey starts with a short supplied key, then extends it using text. The source tests two different choices:

| Model | Key after the starting values |
| --- | --- |
| Plaintext autokey | Runes recovered by that candidate decode |
| Ciphertext autokey | Runes from the observed encrypted text |

The conditional-skip rule can advance past up to three key positions when those positions would produce a repeated ciphertext rune. The source beam keeps up to 450 candidate paths, ranked by cumulative English quadgram score. It returns the first highest-ranked path, then compares that path's normalized score with the gate. Those two rankings need not agree.

## Why this does not rule out autokey

We encrypted known messages, then asked the decoder to recover them. Across 360 checks, the outcome depended on whether both programs followed the same rules:

| Known-message cases | Result |
| --- | --- |
| 113 compatible cases | Every message recovered completely |
| 247 incompatible cases | The correct message was impossible under the decoder's rules |

For example, one check needs **the third plaintext rune to decode the third plaintext rune**. The encoder already knows that rune; the decoder has recovered only the first two. Keeping more candidate readings cannot resolve that mismatch.

These are checks using two known passages, not new LP2 readings. They explain a limit of this program; they do not show that autokey itself is impossible.

## Where the rules disagree

The plaintext encoder can read the whole known message, including runes not yet recovered by its decoder. The ciphertext encoder uses zero when a requested rune has not yet been produced; its decoder instead reads that position from the complete observed ciphertext. This is different from losing a valid reading through beam pruning. Failed cases are retained, not retried or replaced.

In the saved synthetic Warning example with a one-rune starting key, output rune 3 asks for key position 4. That requires plaintext rune 3, but the decoder has recovered only the first two runes. The encoder reads value 24; the decoder has no value yet. Here 24 is a zero-based alphabet index, not a prime value.

## A passing score can still be wrong

Passing a score is also not proof of correct text. Ciphertext-autokey cases passed 99 scores but recovered only 59 readings: 40 accepted outputs were wrong. Eight ciphertext-autokey checks with the fixed wrong primer also passed. Both original 90-rune source gates passed, although the same source ciphertext-autokey fixture recovered only about 67% of its complete reading.

## The complete source result

The highest returned score was −6.627310296014692: LOSS as the starting key, ciphertext autokey, sign −1 on [LP2-49](#/page/lp2-49). It remained below −5.5. All 9,900 returned outputs and scores are saved.

The additional normalized-score check covered 2,099,107 retained terminal hypotheses. It improved the returned score in 5,564 cases, but none crossed the same gate. This diagnostic checks only paths retained by the source beam; it does not change the historical selection or recover discarded paths.

The plaintext decoder can skip at most starting-key length minus one positions across a whole message. With a one-rune starting key, it cannot skip at all. The 3,190 such settings are retained as part of the source grid and identified as rigid plaintext autokey, rather than counted as a new skip mechanism.

## Scope and reproduction

The source starts afresh on each nonempty segment, reads forward, and uses all 29 one-rune starting values plus 16 literal words. There is no alphabet reversal, starting-offset scan or short target screen in this driver. LP2-50 contributes no runes to this source transcription; later segment ordinals are mapped to LP2-51 through LP2-55.

This is a complete measurement of the specified source algorithm, not a general rejection of autokey, skipped-position ciphers or other languages. No complete-search null probability was calibrated. The encoder/decoder mismatch limits what the source's recovery gate can support.

[Reproduction instructions](experiments/records/autokey-skip-family/PORTABILITY.md) separate the saved-results check from a full temporary-directory replay with exact external transcription. The downloads retain every control outcome, frozen protocol, source bytes, all winning outputs and independent native checks.
