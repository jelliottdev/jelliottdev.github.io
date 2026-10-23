# LP2-54: do the simple header autokeys make an eight-rune word?

The red opening of [LP2-54](#/reader/lp2-54) has a single rune followed by eight: `ᚪ-ᛗᛝᛞᛡᚦᛉᛁᛗ`. A reported attempt proposed **A**, **I** or **O** for the first plaintext rune and considered autokey feedback for the next word. The [earlier fixed-rule record](#/experiments/lp2-54-header-feedback) calculates all nine output runes for both simple feedback rules. Here the narrower question is whether **any of those six eight-rune outputs is an English word in a fixed corpus**.

![The six fixed outputs, all without a corpus match.](experiments/records/lp2-54-header-dictionary/header-cribs.svg)

**Result: zero of six match.** The pinned corpus has **19,715 distinct eight-rune spellings** among 138,466 entries. The same six calculations on **all 13** visible one-rune/eight-rune word pairs across LP2-00–55 also produce no corpus matches. Both planted `A MOUNTAIN` controls decode correctly, one for each feedback rule. The all-page comparison is context, **not a p-value**: those 13 pairs were not random draws from English.

The rules are exact. Convert the nine cipher runes to zero-based Gematria Primus indices modulo 29. Choose A, I or O at position zero, which fixes the primer. With ciphertext feedback, each later plaintext index is the current cipher index minus the *previous cipher* index. With plaintext feedback, subtract the *previous plaintext* index instead. Keep the printed one-plus-eight break. We looked up only the resulting eight-rune sequence, after mapping the corpus's alternate J rune to the manuscript's J rune. No word was selected to influence a key or an alignment.

| First rune | Feedback | Eight-rune output, by GP label | Corpus match |
| --- | --- | --- | --- |
| A | Ciphertext | A TH TH R R EO AE N | No |
| A | Plaintext | A Y Y U U P Y OE | No |
| I | Ciphertext | A TH TH R R EO AE N | No |
| I | Plaintext | N EO J T S EA J H | No |
| O | Ciphertext | A TH TH R R EO AE N | No |
| O | Plaintext | T C/K E N OE NG E U | No |

The repeated ciphertext-feedback row is expected: after the first position, that rule depends only on adjacent ciphertext, so changing the first-rune crib cannot change the second word. The pinned corpus is a finite vocabulary, not every possible English spelling or phonetic rune transliteration. A word miss therefore excludes **these two literal one-step rules with these first-rune choices and this corpus**. It does not test the source discussion's unspecified C/K/D functions, extra cipher layers, changed word boundaries, interruption positions, or a complete LP2 reading. A more flexible search must state its transforms and total candidate count before judging a hit.

## Reproduce

Use the [experiment bundle](downloads/experiments/lp2-54-header-dictionary.zip) or a checkout, then run:

```text
python experiments/records/lp2-54-header-dictionary/run.py --check
python experiments/records/lp2-54-header-dictionary/check.py
python experiments/records/lp2-54-header-dictionary/plot.py --check
```

The [plan](experiments/records/lp2-54-header-dictionary/plan.json) specifies the rules and exclusions. The [full result](experiments/records/lp2-54-header-dictionary/results.json) lists every eligible page pair and all 78 outputs. The preserved word list is separately attributed to [Liber Primus Crib Assist at revision `9c10caf`](https://github.com/mortlach/Liber-Primus-Crib-Assist/tree/9c10cafce02e512840cc9e173127930594a56281/data/1_grams-full); it is not claimed to be the exact dictionary used by the original reporter.
