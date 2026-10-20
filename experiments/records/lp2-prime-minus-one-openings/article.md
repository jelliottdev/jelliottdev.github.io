# Can the prime-minus-one recipe be reused?

LP2-56 supplies a concrete reason to try a numerical keystream: its known reading subtracts successive primes minus one from rune indices. This experiment asks a narrower, reproducible question: does that arithmetic, without interruptions, recover a familiar opening on any rune-bearing page from LP2-00 through LP2-55?

The answer for the declared search is **no exact opening matches**. All 3190 candidates completed, giving 28,710 comparisons against nine known openings. This does not mean the candidates have been judged unreadable, or that prime-based ciphers have been ruled out.

## What was tried

Each rune is represented by its zero-based position in the 29-rune alphabet. These are alphabet indices, not Gematria Primus prime values. Read [rune indices and prime values](#/wiki/rune-values) before reproducing the calculation if that distinction is unfamiliar.

For rune position j and starting offset s, the output is:

```text
output[j] = (input[j] + direction × (prime[j + s + 1] − 1)) mod 29
```

Here prime[1] is 2. Offset zero therefore starts with shifts 1, 2, 4, 6, 10. Offset one starts with 2, 4, 6, 10, 12. The sequence does not repeat after 29 terms: testing offsets 0–28 is a finite choice, not an exhaustive phase search.

| Choice | Declared setting |
| --- | --- |
| Pages | LP2-00–55; LP2-50 has no recognized runes and contributes no candidates |
| Input order | All archived runes, including headings, in transcription order |
| Starting offsets | Every integer from 0 through 28 |
| Arithmetic | Subtraction and addition, modulo 29 |
| Advancement | One term per rune; no copied runes or interruptions |
| Boundaries | Restart on each page; do not restart at words or rows |
| Match rule | First 12 output indices equal a complete declared 12-index opening |

There are 55 nonempty pages × 29 offsets × two directions = 3190 candidates. Every full output sequence is retained, including candidates that fail the opening test.

## What counts as a match?

The nine reference openings come from the archived readings of Warning, Welcome, Some Wisdom, the first koan, Loss of Divinity, the second koan, Instruction, LP2-56 and LP2-57. Their exact vectors and trace hashes are frozen in the plan. Spaces and Latin spelling are not compared.

An opening test answers “does this reproduce one of these specific beginnings?” It cannot answer “is there meaningful text here?” A correct decoding with a different beginning would fail this test. There is no language model, English score, significance threshold or selection of attractive partial words.

## A known-answer control

Before treating the result as usable evidence, the independent checker verifies the first 56 runes of LP2-56 against its archived trace. For example, the first four input indices are 25, 11, 22, 15. Subtracting 1, 2, 4, 6 gives 24, 9, 18, 9: A N E N.

At zero-based rune ordinal 56, the known LP2-56 recipe copies a rune without advancing the prime schedule. This control deliberately stops before that interruption. The experiment does not assume an equivalent exception on an unsolved page, and does not claim to reproduce the entire LP2-56 reading with uninterrupted subtraction. See the [full prime-minus-one recipe](#/wiki/prime-minus-one) for the complete control.

## Result and checks

All 28,710 exact comparisons failed to match. The pre-run plan and runner were committed as ea5b0f2 before execution. No offsets, target openings or acceptance rules changed after inspecting the result.

A full second execution reproduces the saved JSON exactly. A separate checker generates the prime sequence by trial division, rather than the runner's sieve. It audits every saved candidate by undoing its arithmetic, checks that every declared page/offset/direction combination appears exactly once, and verifies the nine opening vectors against their source CSV files. This is computational verification; human review remains pending.

## Reproduce it

Download or clone the repository, open a terminal at its root, and run with Python 3.12:

```sh
python experiments/records/lp2-prime-minus-one-openings/run.py --check
python experiments/records/lp2-prime-minus-one-openings/check.py
```

Both commands use local files and the standard library. They do not call an AI service. To write a fresh result without replacing the reviewed one:

```sh
python experiments/records/lp2-prime-minus-one-openings/run.py --output prime-minus-one-rerun.json
```

The output path must not already exist. The saved result identifies every candidate by page, offset and direction, alongside its complete output indices and matching-opening list.

## What remains open

Different plaintext beginnings, later starting offsets, interruptions, heading removal, reversed input, cross-page continuation and composition with another cipher are outside this test. Replacing prime-minus-one with primes, Fibonacci numbers or totients also changes the procedure and requires a declared variant with its own result page.

Before expanding a range, state why the new range is useful. Before adding exceptions, specify how many and where they may occur. Otherwise the search can keep adapting to accidental fragments without a clear stopping rule.
