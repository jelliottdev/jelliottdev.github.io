**None of the 234 complete-page results passed the source's English-score test.** This search moved the starting position of four keys derived from the manuscript's number grid, allowing key values to be skipped under a fixed repeated-rune rule. It checked the first 50 runes at **30,112 settings**; only 234 passed the short screen and received a whole-page decode. Their strongest score was **−6.361 on [LP2-49](#/page/lp2-49)**, below the source's −5.5 bar. This bounded search supplies no supported reading.

![30,112 short screens select 234 complete-page checks. None clears the English-score bar; the strongest complete output on LP2-49 scores −6.361.](experiments/records/payload-phase-skip-grid/payload-phases.svg)

## What moving the key means

The source preserves two different 256-byte interpretations of the LP2-49–51 number grid. Each is used forward and backward, giving four keys. A byte becomes its remainder modulo 29. The decoder normally consumes the next key value for each rune. It may skip up to three values before accepting the next—but only if **every skipped value would have repeated the preceding ciphertext rune**. The beam retains paths using an English four-letter score. This is a candidate rule, not evidence that the manuscript actually used such skips.

An [earlier payload-key experiment](#/experiments/dukotah-payload-key-skip) started all four keys at position zero. This source branch also tries later starting positions. Its “all-offset” label is broader than its code: for a page of L runes it uses starts `0…max(1,268−L)−1`. Long pages often receive only start zero. The 66-rune LP2-49 page receives starts 0–201. The 55 pages contribute 1,882 page/start pairs, multiplied by four keys, both arithmetic signs and Atbash off/on to give 30,112 short screens.

There are **880 zero-start labels overlapping the earlier experiment** and **29,232 labels with nonzero starts**. The algorithms are not identical even at zero: the earlier record used full beam 320 without a short gate and a different finite key allocation. This source branch repeats each 256-value key seven times, giving exactly 1,792 values; no tested path reaches zero padding. Its short beam is 60, with strict score greater than −6.5; selected pages use full beam 300, with strict score greater than −5.5. Parts A and C of the source program are excluded.

The strongest returned complete output uses the reversed first payload, subtraction, Atbash and start 23 on LP2-49. Starts count from zero: start 23 begins at the 24th stored key value. The strongest short output, −5.833, uses that same reversed payload on [LP2-54](#/page/lp2-54), addition, no Atbash and start 16; its short success does not become a full-page confirmation. These are settings of one payload-key idea, not thousands of independent solving ideas.

## Known-message checks

Before the manuscript run, we froze and executed **1,616 decoder controls**: four keys, both signs and every phase 0–201, with a predetermined choice between two complete audited readings. We used the first seed in the frozen range that kept every planted step within three key skips; all attempts and all outcomes are retained. Every plant was eligible, **1,555 contained genuine skips**, and 61 contained none. Atbash inversion is algebraically the same decoder problem; 16 endpoint cases also reproduce the full output exactly. Duplicating every Atbash twin would not provide independent power evidence.

All 1,616 controls passed the short and full score gates, but **1,540 recovered every rune correctly**. In the other 76, the true reading was valid and still present in the final beam at ranks 2–5. The returned alternative had a strictly higher cumulative score in every case; there were no ties or pruned true readings. In 20 cases it had a worse normalized score than the true reading. A fixed wrong key passed both gates in **0 of 1,616** controls. These checks demonstrate useful recognition under the rule, with a clear exact-recovery limitation. They are not calibration of the complete manuscript search or proof that every known message would survive its page-length selection bounds.

## Independent checks and a separate score audit

The source run took **18.90 seconds**. Its page arrays match the existing pinned transcription. A separate scalar implementation reconstructs every selected complete-page output and the best short output, re-scores every saved output, and independently reconstructs all 1,616 planted ciphertexts and skip lists. It checks the original page-specific phase bounds rather than replacing them with all 256 phases. All 2,048 complete signed cycles across four payload variants and 256 possible phases are distinct; no phase/sign quotient was used to omit target settings.

After the original run, a separately frozen diagnostic inspected every retained terminal candidate. Across **34,827 candidates**, none passed −5.5; the best normalized candidate is also −6.361. Normalized ranking chooses a different candidate in 170 of the 234 full searches. The source's original cumulative-score selections remain unchanged. The independent checker also reconstructs and verifies each best-normalized terminal witness. This audit does not recover paths pruned earlier or decode rejected short screens as full pages.

The [frozen target plan](experiments/records/payload-phase-skip-grid/frozen-plan.json), [control plan](experiments/records/payload-phase-skip-grid/control-plan.json), [results](experiments/records/payload-phase-skip-grid/results.json) and complete output ledger retain the exact inputs and decisions. Original source, model, payload bytes and MIT license are bundled.

This result concerns four payload constructions, the executable phase bounds, source skip rule and fixed English scorer. No global null calibration was run. It does not exclude other grid interpretations, phases, key clocks, languages or encryption families, and does not establish an OTP explanation.

## Reproduce offline

With Python 3 and NumPy, from the checkout or extracted bundle:

```text
python experiments/records/payload-phase-skip-grid/controls.py --check
python experiments/records/payload-phase-skip-grid/run.py --check
python experiments/records/payload-phase-skip-grid/audit_terminal.py
python experiments/records/payload-phase-skip-grid/check.py
python experiments/records/payload-phase-skip-grid/plot.py --check
```

The control replay compares all numerical and recovery fields while ignoring only timing fields. The target replay compares every output byte and deterministic report field without overwriting expected results. No external source cache is needed.
