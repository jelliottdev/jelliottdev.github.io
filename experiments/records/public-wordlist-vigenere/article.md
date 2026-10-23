# A public 43-key Vigenère sweep

An archived attempt tried Liber Primus-related words as repeating Vigenère keys. Its [README](https://github.com/LiberPrimus/Failed-Attempts/blob/d219a8099f8d24e52496e9ee3456ed9980893884/bruteforce/vigenere/README.md) describes a wordlist; its [output archive](https://github.com/LiberPrimus/Failed-Attempts/blob/d219a8099f8d24e52496e9ee3456ed9980893884/bruteforce/vigenere/vigenere-bruteforce-results.zip) contains **43** rune keys across 58 page files. The archive includes an additional DIVINITY key after the listed words. We take the keys from the archived output, rather than silently reducing the set to the README list.

## Finding

![A fixed-key sweep: 43 keys across 55 rune-bearing unsolved pages, with no 12-rune known-opening match.](experiments/records/public-wordlist-vigenere/key-sweep.svg)

The **complete decoded rune streams** match the pinned public output in all **2,494 page–key cases** (43 keys across 58 archived pages). That includes **2,408 cases** on LP2-00–55; LP2-50 contains only the alphanumeric grid and has no rune output. None of the 2,365 rune-bearing page starts equals any of nine predeclared, 12-rune known-reading openings: **0 of 21,285 comparisons**. A planted MOUNTAIN plaintext encrypts and decrypts correctly with the first source key.

This verifies the public arithmetic throughout each archived output and rules out **these keys, at page-start phase zero, for these nine exact openings** on our transcription. It does not mean that every wordlist Vigenère attempt has failed. A different key, phase, word-boundary reset, alphabet, page segment, or plaintext beginning is outside this check. The source's “no good result” is an editorial observation, not a numerical language score, so we do not present it as a measured threshold.

## What was done

For every rune position *j* on each page, we computed plaintext index `P[j] = C[j] − K[j mod length(K)] (mod 29)`. Non-rune marks and the number square remain visible but do not advance the key. We kept the GP rune order and the printed page boundaries fixed. The [plan](experiments/records/public-wordlist-vigenere/plan.json) pins all 43 rune keys and the public repository revision. The saved [results](experiments/records/public-wordlist-vigenere/results.json) give every LP2-00–55 page/key prefix and its input hash. The independent [check](experiments/records/public-wordlist-vigenere/check.py) recomputes those prefixes; with the source ZIP, it compares the **full Latin rune-label stream** on all 58 archived pages. The [source-output certificate](experiments/records/public-wordlist-vigenere/source-output-certificate.json) records that wider audit. The archive uses both `IA` and `IO` for one GP rune. We normalize that label, omit the separately structured eight-cell alphanumeric grid rows, and keep letters in lines with inline numbers; rune labels are not unambiguously separable by greedy spelling, so the comparison uses complete joined label strings.

This is related to the [two known Vigenère keys and nine openings](#/experiments/lp2-known-vigenere-keys), but it is a different fixed source key list and a narrower phase rule. The nine openings are a diagnostic: their absence does not prove that no decoded output contains meaningful text elsewhere.

## Reproduce

From the repository root, run `python experiments/records/public-wordlist-vigenere/run.py --check` and `python experiments/records/public-wordlist-vigenere/check.py`. To verify every complete archived output, download the ZIP from the pinned GitHub revision and pass it with `--source-archive PATH` to the checker; the source ZIP and page inputs are hash-checked.
