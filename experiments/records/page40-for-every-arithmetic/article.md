# What does the LP2-40 “FOR EVERY” calculation actually establish?

A [reported attempt](#/wiki/reported-attempts?section=page40-for-every-mobius) reads the first two rune groups on [LP2-40](#/reader/lp2-40) as **FOR EVERY**. It interprets mirrored border work as a reason to use Atbash, floral details as the numbers 13 and 31, and their difference, 18, as a shift. It then adds a prime-minus-one stream, treats the initial F as a skipped zero, and suggests a Möbius-directed running key for the difference still needed. Those links from artwork to operations are the solver's proposed interpretation; this audit does not establish them as intended clues.

The source discussion itself describes the example as a working theory built partly backwards from a desired reading. Its linked spreadsheet was described as changing over time. We identify the preserved discussion by SHA-256 `2338de900f4ec231d42791c988640317241880675b35ff68af42ee162cb6573a`; the file is not redistributed here. The replay uses the numerical rows printed in that discussion, the [archived LP2-40 transcription](#/page/lp2-40), and the stored Gematria Primus table.

## Eight positions, one fixed calculation

The first two archived groups contain three and five runes. Their indices are `0, 9, 19 / 26, 6, 23, 25, 8`, matching the source's quoted ciphertext row. The proposed **FOR EVERY** indices are `0, 3, 4 / 18, 1, 18, 4, 26`. On the seven positions after F, shifting each proposed plaintext index by 18 and reflecting with Atbash gives `7, 6, 21, 9, 21, 6, 13`. Adding the source's prime-minus-one stream modulo 29 gives the intermediate row `0, 8, 8 / 25, 15, 2, 18, 0`.

![The fixed rule is compared with eight archived indices. Seven non-F outputs differ; the final row is a residual derived from the observed ciphertext.](experiments/records/page40-for-every-arithmetic/first-eight-trace.svg)

The fixed layers match **zero of seven non-F positions**. The initial F matches because the source holds it at zero rather than transforming it. Subtracting the intermediate row from the observed ciphertext yields residuals `0, 1, 11, 1, 20, 21, 7, 8` modulo 29. The source writes `−8` instead of `21` at the sixth position; these are the same modulo 29. These residuals are calculated *after looking at the ciphertext*. Adding them back necessarily reconstructs the target and is not yet evidence for a running-key rule.

The proposed phrase's GP sums are **FOR = 20** (composite), **EVERY = 251** (prime), and **FOR EVERY = 271** (prime). Thus the whole phrase satisfies a prime-sum filter, while both words individually do not. A prime sum is a property of this candidate, not an independent reading of the runes.

## Where the replay stops

The discussion does not fix the Möbius argument or starting point, how neighboring values form the proposed trigram state, which of the eight possible key formulas belongs to each state, how signs and zero are treated, or exactly when the stream advances over F and separators. Its later notes explore modified Slidefair, Quagmire-like matrices and a Fibonacci autokey as different follow-ups; those are **not** tested here. The incomplete spreadsheet and absent fixed state table prevent an honest end-to-end replay of the proposed running key. The source itself says the state flexibility could make the arithmetic fit.

To turn the running-key idea into a test, choose a complete state table and seed **before** inspecting additional text; specify plaintext-versus-ciphertext feedback, order of operations, F handling and word boundaries; then compare a continuous output on held-out page text with matched controls. A crib fit on these eight positions alone cannot do that work.

## Reproduce this audit

From the repository root or [downloadable experiment bundle](downloads/experiments/page40-for-every-arithmetic.zip), run:

```text
python experiments/records/page40-for-every-arithmetic/run.py --check
python experiments/records/page40-for-every-arithmetic/check.py
python experiments/records/page40-for-every-arithmetic/plot.py --check
```

The [plan](experiments/records/page40-for-every-arithmetic/plan.json) pins the source's printed rows, input hashes, fixed formula, success criterion and stopping rule. The [complete result](experiments/records/page40-for-every-arithmetic/results.json) lists every intermediate and fitted difference. The checker independently reads the rune text, recomputes the seven transformed indices and verifies each congruence and prime sum. This is an **arithmetic audit of one proposed opening**, not a disproof of every artwork-based or running-key method.
