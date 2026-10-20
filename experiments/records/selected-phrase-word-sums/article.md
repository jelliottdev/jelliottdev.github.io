# Selected phrase and MYRMELEONTIDAE word sums

This variant changes the baseline's candidate list to five supplied words: PROVE, WORTHIER, FIND, TRUTHS and MYRMELEONTIDAE. The first four were proposed against totals 131, 151, 151 and 131; the last against 809. It checks those selected matches without claiming that the resulting phrase or name is recovered plaintext.

## What changes from the baseline?

The [baseline word-sum audit](#/experiments/mixed-square-word-sums) tests sixteen other supplied word-and-total pairs, including FIND. This variant retains the same 29-label alphabet, V-to-U normalization, exhaustive segmentation procedure and prime-value summation. Only the candidate list and proposed targets change. FIND is intentionally retained as a shared check.

The candidate list was fixed before enumeration, but the supplied words were already selected for their claimed numerical matches. This is an exploratory audit, not an unbiased measure of how frequently words match these targets.

## All ten segmentations

Every segmentation is retained below. A slash separates rune labels; adjacent Latin letters inside one label belong to a single rune.

| Candidate | Rune labels | Sum | Proposed target matched? |
| --- | --- | --- | --- |
| PROVE | P / R / O / U / E | 131 | Yes |
| WORTHIER | W / O / R / TH / I / E / R | 151 | Yes |
| WORTHIER | W / O / R / T / H / I / E / R | 228 | No |
| FIND | F / I / N / D | 151 | Yes |
| TRUTHS | T / R / U / TH / S | 131 | Yes |
| TRUTHS | T / R / U / T / H / S | 208 | No |
| MYRMELEONTIDAE | M / Y / R / M / E / L / EO / N / T / I / D / A / E | 809 | Yes |
| MYRMELEONTIDAE | M / Y / R / M / E / L / EO / N / T / I / D / AE | 746 | No |
| MYRMELEONTIDAE | M / Y / R / M / E / L / E / O / N / T / I / D / A / E | 842 | No |
| MYRMELEONTIDAE | M / Y / R / M / E / L / E / O / N / T / I / D / AE | 779 | No |

All five targets are achievable, each by one segmentation. PROVE and FIND each have only one segmentation under the declared rules. WORTHIER and TRUTHS each have two; MYRMELEONTIDAE has four.

## The 809 match requires a particular segmentation

MYRMELEONTIDAE gives 809 when EO is combined but the final A and E are separate. Combining both EO and AE gives 746. Separating both pairs gives 842; combining only the final AE gives 779. These alternatives differ because a two-letter rune's prime value is not the sum of its two separate letters' values.

A converter that always consumes the longest available label would choose EO and AE and return 746. A converter that always treats each Latin letter separately would return 842. The proposed 809 result is therefore possible within the exhaustive search, but it is not determined by the spelling alone. No evidence here selects that segmentation as the manuscript's intended representation.

## What the phrase match establishes

The matching totals for PROVE WORTHIER FIND TRUTHS are 131, 151, 151 and 131. That verifies four arithmetic assignments. It does not recover their order, grammar or intended meaning from the square. Choosing words for their fitting totals and then observing that those totals are prime is not a second independent test: the target numbers already supplied that property.

The [mixed-square guide](#/wiki/magic-squares) distinguishes LP1-05's 1033 square, LP1-16's 3301 square and the separate LP2-15 panel. This variant associates the first four targets with LP1-05 and 809 with LP1-16; it does not move the red 3299 from LP2-15 into either square. A claimed thematic relation of a word to insect imagery would require separate evidence and is not tested here.

## Reproduce and inspect

```text
python experiments/records/selected-phrase-word-sums/run.py --check
python experiments/records/selected-phrase-word-sums/check.py
```

The runner is byte-identical to the baseline runner and reads this variant's plan. Without `--check`, it prints the complete JSON report. The independent checker enumerates every cut/no-cut choice between Latin letters, rejects pieces absent from the alphabet, and verifies all retained segmentations and totals. Both commands passed in the extracted reproduction bundle. Python's standard library is sufficient; no dictionary download or hosted AI is involved.

## Limits and next variants

No alternative words, synonyms or dictionary entries were searched. No cipher was applied to the manuscript, and no null model estimates the surprise of the selected words. The finding neither proves an intended phrase nor shows that these are the only fitting words.

A broader word search must pin its vocabulary, normalization and segmentation policy, then retain all matches. A fixed longest-label policy would be a different variant. A cipher test using these candidates must specify the target pages, transform, key advancement and success criterion. The [rune-length bounds](#/wiki/prime-sums?section=length-bounds) can rule out impossible lengths before a dictionary search starts.
