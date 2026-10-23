# Multi-rune feedback and autokey

A feedback cipher can derive each new key symbol from earlier symbols. [This published screen](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round12/C1/RESULTS.md) tested whether LP2 behaves that way when the key depends on the previous two to six runes.

## Finding

**None of the 23,520 source configurations produced a convincing English reading.** The strongest result scored **−6.299**, below the source's required **−5.500**. It came from a **66-rune segment**, not the continuous manuscript: a five-rune plaintext-history XOR rule on the reversed segment, with an all-six seed. The source program successfully recovered all **21 planted cases** at history length three and gave wrong-rule decodes much lower scores.

![The planted control clears the score threshold; the highest-scoring LP2 candidate remains below it.](experiments/records/public-multihistory-feedback/scores.svg)

These are English quadgram scores; higher means the transliterated output resembles the training text more closely. The strongest short fragment is still well below the planted English sample. A score by itself would never establish a solution without a coherent continuation.

## How the tested rules work

At each position, the program reads the previous *k* symbols, passes them through one of seven fixed functions, then adds or subtracts the resulting value modulo 29. The seven functions are an index sum, prime-value sum, XOR, prime-of-index-sum, prime-of-prime-sum, last-symbol difference and alternating sum. It tries three kinds of history: the visible ciphertext, the plaintext decoded so far, or the modulo-29 sum of the two. The source also tries both directions of the rune stream and both arithmetic signs.

![A five-rune history is mapped to a key value, then combined with the next ciphertext rune to produce a proposed plaintext rune.](experiments/records/public-multihistory-feedback/feedback.svg)

The screen covers the **12,956-rune continuous unsolved stream** plus its **55 nonempty source segments**. For ciphertext history, symbols after the first *k* positions do not depend on the initial seed. For plaintext and mixed history, the source tries only the **29 all-equal seeds** `0…0` through `28…28` at each *k*, then keeps the best score. That is a thin slice of the possible **29^k** initial states. In particular, a wrong initial plaintext state need not “lock on” to the correct state later; the source's broader claim that a genuine autokey would necessarily reveal itself under these seeds is not established by this test.

The source's 200 shuffled controls score the raw full stream, while its reported best is selected from thousands of configurations, many on short segments. That shuffle maximum is not a full best-of-grid null. The result is therefore **no supported English reading in the executed grid**, not a statistical exclusion of every feedback cipher.

## Reproduce

Download the experiment ZIP and run from its extracted folder:

```sh
python experiments/records/public-multihistory-feedback/run.py
```

It runs the 21 planted controls before the full sweep, then checks the saved result against the separately archived source output. The independent checker reconstructs the 12,956 source rune indices and **recomputes the winning XOR/plaintext-history decode and score** without calling the source's feedback decoder. For a quick check of the packaged outputs, run `python experiments/records/public-multihistory-feedback/check.py`. The full sweep takes several minutes.

The code, transcription and scoring table are included from [Dukotah/cicada3301 revision f08b20b](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round12/C1), with the repository's license. This record matches that program's executed parameters; it does not claim to rule out other functions, alphabets, seed states or non-English plaintext.
