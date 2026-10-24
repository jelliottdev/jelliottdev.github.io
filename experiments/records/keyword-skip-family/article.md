# Keyword search with skipped key positions

None of the 619,080 short checks passed the source's English-score gate. The search therefore ran no full-page decodes. It tested 623 keyword labels, including different starting positions, arithmetic directions and an optional rune-alphabet reversal.

The controls show an important limitation: a passing English score need not recover the right text. All 617 known-key tests passed the score gates, but only 575 recovered their known reading completely. These tests reuse two known passages. Three of four searches across the complete vocabulary recovered the full reading.

![Passing an English score is not the same as recovering the known reading.](experiments/records/keyword-skip-family/control-recovery.svg)

## What the search did

This reproduces the pinned public `keywords_skip.py --full` fast branch. It tries each keyword as a repeating numeric key. When the proposed next ciphertext rune would repeat the previous one, the decoder may skip up to three key positions under the source's conditional rule. Each page starts afresh.

Every keyword phase receives a check of the first 90 runes, or the complete segment if shorter. The beam retains up to 300 candidate paths. For each keyword, sign and alphabet direction, only the phase with the best returned normalized score can continue; it must score strictly above −6.0. A promoted phase would receive a complete-page beam of 500 paths and a strict −5.5 final gate.

All 623 labels and 2,814 phase labels were retained, including aliases. They encode 617 distinct key arrays. Across the 55 nonempty source segments, both signs and both alphabet directions, that gives 619,080 screens and 137,060 best-phase selections. LP2-50 contributes no runes to this source transcription; later source segment numbers are mapped to LP2-51 through LP2-55.

## Result and limits

The highest screen score was −6.020535494918678, from EVEN on [LP2-10](#/page/lp2-10), sign +1, unchanged ciphertext alphabet, phase 3. It fell below the first gate. This is a score of a short candidate, not a recovered message. The complete saved score grid and phase selections are available in the downloads.

The source ranks beam paths by cumulative score, then evaluates its returned path by normalized score. Those rankings can disagree. Among the failed controls, 37 retained the correct complete reading but returned a higher cumulative-scoring alternative; seven chose the wrong starting phase. Four incorrect winners had worse normalized scores than the retained correct reading. A separate normalized-terminal diagnostic is retained for promoted full runs; there were no such target runs to inspect.

The result covers this finite vocabulary and this exact selection procedure. It does not exclude other keywords, different skip rules, phases rejected by the short gate, other languages or periodic ciphers generally. No complete-search null probability was calibrated here. The unchanged historical gate passed, but the broader controls prevent interpreting its no-hit result as an all-key recovery guarantee.

## Reproduction

The bundle includes the frozen protocol, purpose amendment, source files, all synthetic controls, score arrays and independent audits. [Reproduction instructions](experiments/records/keyword-skip-family/PORTABILITY.md) distinguish a quick saved-results check from a complete temporary-directory replay with the exact external transcription. No new manuscript search settings are selected during replay.
