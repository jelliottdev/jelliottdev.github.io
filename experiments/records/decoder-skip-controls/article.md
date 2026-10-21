## Can a correct key still fail?

Yes, under a mismatched decoding rule. This experiment starts with known rune sequences, encrypts them using four precisely specified mechanisms, and asks what rigid subtraction and a skip-aware beam decoder recover. Knowing the answer lets us measure exact recovery rather than judging whether a candidate merely sounds plausible.

All ordinary-addition controls recover exactly with the correct key. With key skipping and single-value keys, the beam allowing three skips recovers 26 of 27 plants exactly, while rigid subtraction recovers one. Repeating each key value four times changes that result: the same beam recovers eight of 27, with the true recorded alignment outside its transition rules in the other 19. Increasing beam width from 16 to 64 does not repair that structural limit.

These findings concern the declared artificial encoders. They do not show that the unsolved manuscript uses key skipping, rewriting, or any particular key generator.

## Four ways to consume the same key

Every operation uses rune indices modulo 29. Ordinary addition emits `c = p + k`; subtraction recovers `p = c − k`. A key slot is a position in the generated sequence, not its numerical value. Several slots can hold the same value.

| Encoder | What happens when the proposed ciphertext repeats the previous rune? | Key alignment |
| --- | --- | --- |
| Ordinary addition | Emit it unchanged. | One slot per plaintext rune. |
| Key skipping | With probability 83/100, reject that key slot and retry the same plaintext rune. | Rejections consume additional slots. |
| Value rewriting | With probability 83/100, add one to the proposed ciphertext value modulo 29. | Still one slot per plaintext rune. |
| Unrelated advance plus skipping | Apply the skip rule, but also consume one extra slot halfway through the plaintext, regardless of repetition. | Contains an advance that the collision-only model may not permit. |

The first emitted rune has no predecessor. The rejection draw occurs only on a collision. Each plant resets its state, and every draw, rejected slot, accepted slot and rewrite is preserved in the report. Exhausting the key is an error; no zero padding is allowed.

The key fixture hashes a fixed seed label and counter with SHA-256, then reduces each byte modulo 29. This reduction is biased because 256 is not divisible by 29. It is a reproducible test input, not a claim of uniform randomness or a one-time pad. The second fixture repeats each value across four successive slots. Neither fixture was adjusted to match manuscript statistics.

## What the beam can represent

The rigid decoder consumes one slot at every step. The beam keeps several candidate prefixes. At each step it considers accepting the next key slot, or skipping up to its declared limit. A skipped slot is permitted only when it would have generated a repeat of the preceding ciphertext rune under that candidate plaintext.

Beam width controls how many prefixes survive scoring. The skip limit controls which paths can exist at all. These are different bounds: retaining more paths does not introduce a transition that the model forbids.

We test widths 16 and 64, each with skip limits one and three. Candidates are ordered by cumulative English quadgram score, then lexicographic key-slot path and rune sequence. The final normalized score is reported separately. Because some rune labels contain multiple letters, maximizing cumulative score is not the same as maximizing normalized score. The experiment preserves this declared selection rule rather than changing it after seeing results.

## The complete control grid

The nine known-reading traces supply their first 240 rune indices, or their full length if shorter. Three seed IDs, two key fixtures and four encoders produce 216 plants. Every plant is decoded with the correct and wrong key using all five decoder configurations: 2,160 results. These reuse source texts and are not independent trials from a population.

The figures show every correct-key configuration. The complete summary CSV also includes every wrong-key configuration, all of which produced zero exact recoveries and zero accepted scores. That finite result is not a general false-positive rate and does not calibrate a large key search.

Selected counts below explain the figures; the CSV retains all 80 grouped cells and the JSON retains every individual result. Each cell has 27 plants. “Accepted” means normalized score at least −5.5, not a correct answer.

| Encoder and key fixture | Decoder | Exact | Accepted |
| --- | --- | ---: | ---: |
| Ordinary addition, either fixture | Every tested decoder | 27/27 | 27/27 |
| Skipping, single values | Rigid | 1/27 | 2/27 |
| Skipping, single values | Beam 64 / 3 | 26/27 | 27/27 |
| Skipping, four-slot runs | Beam 64 / 1 | 0/27 | 0/27 |
| Skipping, four-slot runs | Beam 64 / 3 | 8/27 | 18/27 |
| Rewriting, single values | Every tested decoder | 1/27 | 27/27 |
| Rewriting, four-slot runs | Every tested decoder | 0/27 | 27/27 |
| Unrelated advance, single values | Beam 64 / 3 | 2/27 | 22/27 |
| Unrelated advance, four-slot runs | Beam 64 / 3 | 0/27 | 15/27 |

## Why a passing score is insufficient

Rewriting leaves much of the original text intact. The score therefore accepts many candidates even though some rune indices are wrong. This is an especially clear example of why “looks like language” and “reproduces the full plaintext” must be recorded separately. The [scorer-language controls](#/experiments/english-scorer-controls) examine another failure mode: meaningful text in some languages can receive a poor English score.

An admissible true path also need not finish first. In the single-value skip condition with a three-skip beam, every true path is permitted and none is pruned, yet one plant's winning candidate is not exact. A competing retained path scores higher under the declared ordering. The report distinguishes this from structural failure and records the first pruning step if one occurs; no true-prefix pruning was observed in this grid.

An unrelated advance does not always force failure. If its skipped value happens to satisfy the collision rule, the model can represent it. This explains why some plants in that condition still recover. Conversely, a structurally invalid *recorded alignment* is not a proof that no alternative alignment could spell the same plaintext. Exact candidate recovery is measured independently of the encoder's slot path.

## Even the correct key can be ambiguous

A tiny example makes the issue visible without a language model. Work modulo three with key slots `[0, 0, 1]` and always reject collisions. Plaintext `[0, 1]` emits ciphertext `[0, 1]` using slots zero and one. Plaintext `[0, 0]` emits the same ciphertext by rejecting slot one and accepting slot two. The key and ciphertext alone do not distinguish these two plaintexts under this mechanism.

The stored encoder trace resolves that ambiguity for verification because it contains the answer's alignment. A solver does not receive that trace. The trace-assisted inversion check is an oracle control, not an available decryption attack.

## Reproduce and inspect

Download this experiment's ZIP and preserve the directory structure. Python 3 standard-library modules are sufficient; no network access, API, external model download or third-party package is required.

```text
python experiments/records/decoder-skip-controls/run.py --check
python scripts/check_decoder_skip_controls.py experiments/records/decoder-skip-controls/results.json --receipt my-decoder-audit.json
python experiments/records/decoder-skip-controls/plot.py
```

The producer checks every frozen input hash. The independent checker imports no producer functions: it reconstructs source prefixes, generated keys and encoder decisions, replays beam selection, and checks every returned rune sequence and diagnostic. It also recomputes full-text scores using a separate calculation. All 216 plants and 2,160 decoder results passed. Ten small-control tests include exhaustive transition comparisons, long rejection runs, rewrite wraparound, exhaustion, ambiguity, and beam output checked against complete path enumeration. Human review remains pending.

## Scope and next steps

This is a fresh control inspired by [Dukotah's benchmark work](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/benchmark/README.md), not a replication of that repository's reported percentages. Known readings, including any non-prose material within their selected prefixes, are retained without editing. We do not infer manuscript language, identify its cipher, prove a pad construction, or claim that all skip-aware algorithms share these failures.

A later experiment can change the encoder or alignment rule, but must record those changes and test recovery again. Searching many wrong keys also needs a separate control of the *best score from each entire search*, not just a collection of individual wrong-key scores. See [search space and bounds](#/wiki/search-space) for why the size and selection rule belong in the claim.
