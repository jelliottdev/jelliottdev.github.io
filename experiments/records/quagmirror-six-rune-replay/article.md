# How far does the QuagMirror draft run?

**Result.** The pinned public script processes the first **six runes of LP2-00**, then deliberately stops. An independent replay obtains the same index streams and the transliteration **DCBWJO**. That is a match to the draft program's output, not a reading of the page. The code does not run its proposed method across a complete word or page.

The idea combines an autokey calculation with one of nine handwritten 29-symbol substitution tables. At each position, Möbius values associated with the position and a prime-derived totient choose the table. Previous cipher and output symbols feed the next autokey calculation. The first two positions contain explicit overrides in the source. Those choices are retained here; silently removing them would replay a different method.

![A five-row diagram traces the six cipher indices through the autokey indices, selected mirror tables, output indices and Latin fragments.](experiments/records/quagmirror-six-rune-replay/six-rune-trace.svg)

| Stage | Six values |
| --- | --- |
| Archived LP2-00 rune indices | 15, 8, 18, 3, 6, 19 |
| Autokey indices | 15, 28, 2, 10, 3, 14 |
| Output indices | 23, 5, 17, 7, 11, 3 |
| Latin fragments | D C B W J O |

The replay checks the source's first six input indices against this site's LP2-00 transcription. It stores all nine permutation tables and every fixed choice in the [plan](experiments/records/quagmirror-six-rune-replay/plan.json), then calculates each row in the [result](experiments/records/quagmirror-six-rune-replay/results.json). The tables are permutations, but that property alone does not make the output intelligible or prove an encryption mechanism.

This is a **WIP source-version replay**. The repository contains several changing scripts; it would be misleading to combine their rules into one historical "QuagMirror" result. The particular file [Mobius_AT_QuagMirror.py at pinned commit 88ef1e60](https://github.com/sgroveman/cicada3301_lp/blob/88ef1e60b0738b8b28db96bc9dc44dc4da8dd307/Solving%20Attempts/Mobius_AT_QuagMirror.py) has SHA-256 `e317878190994910afbbdc5707a66af73a684b29abdd9d7e443563aba9d15a66`. Its `break` after six processed positions is part of the code, so this record cannot test its remaining page output, any later revisions or proposed thematic keywords. A complete candidate needs one frozen version, a declared rule for every position, full output and an untouched-text check.

Run `python experiments/records/quagmirror-six-rune-replay/run.py --check` from the repository root. Python's standard library suffices. The saved plan and results make this exact six-position variant available offline without shipping the source discussion or changing its unfinished state.
