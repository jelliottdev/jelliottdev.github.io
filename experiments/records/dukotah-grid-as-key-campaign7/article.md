# Do the numbered grid and 2014 onion bytes unlock LP2?

**Finding.** Three pinned Campaign VII programs tried the numbered-grid values and three 2014 onion hex strings as repeating keys for LP2. We replayed their **14,784 fixed cases**. None reached the programs’ English-score flag of **−5.2**. The best scores were −6.720 for the archived grid list, −6.745 for alternative token bases, and −6.597 for a grid–onion XOR key. Higher scores are more English-like under this model; no displayed best output reads as English. Eight **constructed** 120-rune controls decode exactly and clear the flag. They are not eight recoveries of an unchanged known passage.

![Best scores for the three source searches, all below the flag line.](experiments/records/dukotah-grid-as-key-campaign7/comparison.svg)

The source applies each named number stream as a repeating key, reducing its values modulo 29. It tests addition and subtraction, with and without Atbash. In one version, a visible F rune passes through without advancing the key. It scores 55 rune-bearing LP2 pages separately, then their 12,956-rune join. Source segment `p50` corresponds to site **LP2-51**: site LP2-50 has no runes. This is a test of these key clocks and byte readings, not every way the printed grid could be used.

## Three different input readings

| Source program | What became a key | Cases | Best score |
| --- | --- | ---: | ---: |
| A2 token pad | Hard-coded 80+104+72 grid values, sections and selected XOR joins | 4,032 | −6.720 |
| A2 alternative bases | Raw two-character tokens weighted with 59, 60, 62 and 64 | 7,168 | −6.745 |
| B2 onion XOR | Archived 256 grid values XORed with the second, third or fourth 2014 onion hex, plus onion-only keys | 3,584 | −6.597 |

The hard-coded 256-value list and the raw tokens decoded in base 60 **are different byte sequences**. We preserved both instead of treating them as interchangeable evidence. The source’s 59 and 60 formulas both give numbers within 0–255, but byte range is only one check. Four tokens contain `x`, whose digit value is 59: that digit is invalid in conventional base 59. The source calculates those numbers without rejecting the invalid digit. With this digit order and the byte bound, [base 60 is the only valid positional base](#/wiki/alphanumeric-grids): `x` requires a base of at least 60, while the token `4F` requires a base no greater than 60. The 62 and 64 formulas exceed byte range, although the source still reduces all these numbers modulo 29 to make keys. The hard-coded list has 161 distinct values, so it is not a permutation of all byte values.

The B2 program also examines the direct XOR outputs as 256-byte objects. Its five reported streams have 7.113–7.331 bits of empirical byte entropy and 31.6–39.5% printable ASCII. These simple measurements do not establish whether another encoding or later operation hides data there. The source’s `token^onion2^3^4` combination is tried as a key but is not included in that five-stream forensic table.

## What the replay establishes

The three unchanged source programs, run with their pinned corpus, quadgram model and community source text, reproduce their saved outputs. Our separate implementation matches their best candidate, score, per-key maxima, base-range checks, XOR measurements and zero flag counts. It also saves full-plaintext digests; a checker recreates all **14,784** candidate texts and scores using the source helpers and verifies those digests. The 55 site page sequences independently match the source rune-only segments.

For controls, we encrypted a fixed English-derived 120-rune sequence and checked full recovery in every sign, Atbash and F-clock branch. With the F-interrupter enabled, a ciphertext F must be literal and cannot carry an arbitrary plaintext rune. The construction therefore **replaced 3–6 would-be non-F runes with literal F** in each of those four controls; 114–117 positions of the original sequence remain unchanged. The four controls without the interrupter retain all 120. The controls show the declared decoder and score gate work on legal constructed messages; they do not show recovery of the unmodified English sequence under every branch. An XOR identity control checks the byte operation. These control counts and full-message digests were added after review of the initial replay; the LP2 cases, scoring rule and original search bounds did not change.

The score bar is the source’s screen, not a probability of a solution. A short English passage, another language, a different byte reading or a nonrepeating key may escape it. No output from the **declared operations on the declared inputs** reached this English screen. [Earlier grid tests](#/experiments/dukotah-grid-token-roles) treated the bytes as ciphertext or pointers, which is a different question; [the grid-cell comparison](#/experiments/dukotah-grid-cell-adjudication) documents image-based reading differences not substituted into this exact source replay.

## Reproduce

The [plan](experiments/records/dukotah-grid-as-key-campaign7/plan.json) identifies the pinned revision, inputs, transform grid and timing. The plan is retrospective because the original saved results were already visible before this replay. [Results](experiments/records/dukotah-grid-as-key-campaign7/results.json) contain all group maxima, byte checks, control scores and full-grid score digests. From a Liberpedia checkout, run:

```text
python experiments/records/dukotah-grid-as-key-campaign7/run.py --check
python experiments/records/dukotah-grid-as-key-campaign7/check.py --check-site
python experiments/records/dukotah-grid-as-key-campaign7/plot.py --check
```

The required source programs, model and two community text receipts are bundled under this record’s `source/` folder. They come from the pinned [Campaign VII A2](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/corpus/H-branch-recovery/recovered/claude_master-roadmap-libra-qk527u/liber-primus/analysis/campaign7/a2_tokenpad.py), [alternative-base](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/corpus/H-branch-recovery/recovered/claude_master-roadmap-libra-qk527u/liber-primus/analysis/campaign7/a2_altbase.py) and [onion-XOR](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/corpus/H-branch-recovery/recovered/claude_master-roadmap-libra-qk527u/liber-primus/analysis/campaign7/b2_onion_xor.py) programs.
