# LP1 seven-word GP-825 match

One proposed LP2 reading was compared with a seven-word stretch of the solved LP1 warning. This test checks the **LP1 side of that comparison**: how many seven-word stretches have exactly 21 runes and a Gematria Primus sum of 825?

## Result

Among **652** seven-word windows kept within their solved LP1 sections, **one** meets both conditions. It starts at zero-based word 9 of the warning: `YOU CNOW TO BE TRUE TEST THE`. The decoded-rune trace gives it 21 runes, GP sum 825 and zero-based rune-index sum 232. The source discussion reported 716 windows; that denominator does not reproduce with these seven sections and word boundaries. Even joining all 694 words across section breaks gives only 688 possible starts.

![One qualifying LP1 window among 652 section-internal windows](experiments/records/lp1-seven-word-825-census/windows.svg)

The result confirms an exact match in LP1 under the declared trace. It does **not** establish that the proposed LP2 phrase has the stated rune spelling or sum, that the two passages are linked, or that a decryption rule follows. The phrase and numeric criteria were selected during exploration, so `1/652` is a census of these LP1 windows, not a chance probability for the full search.

## Reproduce

Run `python experiments/records/lp1-seven-word-825-census/run.py --check` from the repository root. The [saved census](research/source-intake/lp1-seven-word-825-audit.json) includes all seven section counts and input hashes. Word separators come from the archived runes; decoded symbols come from the published reading traces. The [source note](research/source-intake/lp1-seven-word-825-audit.md) explains the one documented LP1-10 rune swap and the Latin-label spelling difference.
