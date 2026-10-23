# Can numbers left by earlier puzzles act as LP2 keys?

The 2013 telnet puzzle returned a prime list that jumped from **71 to 1229**. The 180 primes between them, a number in the 2012 closing message, and whitespace-count patterns from signed messages are concrete material to try as keys. A published B3 program converted those numbers to rune shifts and tested them against the unsolved manuscript. This record repeats its exact finite search.

## Finding

**None of the 4,032 tested decodes crossed the program's English-score bar.** The strongest scored **−6.757**; the source required a score above **−5.2**. The two runs we deliberately encrypted with one of these same key streams recovered their intended text, including one where an F rune pauses key advancement. Those controls check the arithmetic and F behavior; they do not show that the source's English threshold would detect every genuine LP2 plaintext.

![The nine numeric streams' best English scores all fall below the source's advancement bar.](experiments/records/historical-prime-and-ps-keys/scores.svg)

The horizontal position represents the best score across all pages and settings for each stream. The labels beside the dots are the measured values. A higher number is more English-like under the source's four-letter-pattern model.

## What the search did

The [pinned B3 program](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/corpus/H-branch-recovery/recovered/claude_master-roadmap-libra-qk527u/liber-primus/analysis/campaign7/b3_hints.py) defines **nine** streams: the 2012 P.S. number as individual digits, two-digit groups, or a base-29 integer; all primes from 73 through 1223 and their adjacent differences; and four recorded whitespace-count sequences. It reduces each term modulo 29 and repeats the stream to cover the target. The prime run has **180 values**. Its first differences have **179**.

For each stream it tested each of **55 rune-bearing unsolved segments** separately and their concatenation. It crossed addition/subtraction, Atbash on/off, and two treatments of F: ordinary encrypted rune, or a copied rune that does not consume a key symbol. That is **9 streams × 56 targets × 8 settings = 4,032 decodes**. These are configurations, not independent hypotheses; one target is the union of the others. The original saved file reports only each stream's best score. Our [case ledger](experiments/records/historical-prime-and-ps-keys/cases.jsonl) accounts for every decode and matches the source summary to three decimal places.

The overall winner was the **2013 whitespace sequence** on source segment `p49`, with subtraction, Atbash, and the F interruption rule. Its score remained far below the bar. The 2012 P.S. readings scored no better than **−6.856**; the omitted-prime sequence scored **−6.895**. The complete list is in the figure and [results](experiments/records/historical-prime-and-ps-keys/results.json).

## Why these are called “missing primes”

This is a **telnet-command** observation, not an omission from the 2013 CicadaOS prime-printing script. A preserved [telnet `primes` transcript](https://github.com/neuroretransmit/cicada/blob/ade9a02889ef8acbc8cde8edbfd0a785c369f4c3/2013/004-first-onion/README.md) shows `71 1229` with no intervening values; the archived [`prime_echo` script](https://github.com/cicada-solvers/The-Complete-Cicada3301-Archive/blob/c3127e0e9eb5afbb582d37988d6369fe38429238/2013/additional%20files/Cicada%20OS/cicados/usr_local_bin/prime_echo) explicitly prints 73, 79, and the rest of that run. The telnet transcript is a later preserved copy, not a fresh capture of the original hidden service. It supports the stated sequence but does not authenticate a command still running today.

## What remains open

The result covers the B3 rules, the pinned transcription, and English scored by this model. It does not test page-specific starting offsets, nonrepeating keys, other uses of the prime indices, or a language other than English. The source did not repeat the full 4,032-case selection on null texts, so **−6.757 is a measured best score, not a calibrated probability**. B3 did not use the 2013 onion-cookie hashes, raw PGP packet bytes, or fingerprints as keystreams; those require their own exact byte selection and conversion rule.

## Reproduce

Download the experiment ZIP and run the two commands from a Liberpedia checkout:

```text
python experiments/records/historical-prime-and-ps-keys/check.py
python experiments/records/historical-prime-and-ps-keys/run.py
```

The checker independently rebuilds the nine streams, scores every case from the pinned rune and quadgram files, verifies the source's maxima, and runs two constructed decryptions. The runner executes the unmodified B3 program in a temporary copy and compares its full result JSON with the archived source output. It leaves the saved evidence untouched. The original program and community note are included with the experiment, with their exact file hashes in the [plan](experiments/records/historical-prime-and-ps-keys/plan.json).
