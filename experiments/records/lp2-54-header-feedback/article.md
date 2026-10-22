# LP2-54: what do simple autokey rules make of the red header?

The [reported header-crib proposal](#/wiki/reported-attempts?section=lp2-54-header-autokey-crib) singles out the nine red runes on [LP2-54](#/reader/lp2-54): one rune, then eight. It suggests a first word such as **A**, **I** or **O**, followed by an eight-rune word. The discussion also corrects a consequential distinction: ciphertext feedback uses the previous **ciphertext** rune, while plaintext feedback uses the previous **plaintext** rune. Those are different recurrences even when both are called “autokey.”

This record tests just those two one-step recurrences, without changing the alphabet or selecting words after seeing output. It is a bounded baseline for the larger proposal, not a replay of the proposed search over hundreds of words and unspecified functions.

The clue-to-rule chain has an important break: the **red one-plus-eight layout is visible on the page**, while A/I/O and either feedback recurrence are solver hypotheses. The manuscript does not explicitly assign those letters or tell us to use autokey. That distinction matters when deciding whether a short output would count as evidence.

## Inputs and fixed choices

The archived red prefix is `ᚪ-ᛗᛝᛞᛡᚦᛉᛁᛗ.`. The hyphen separates the first rune from the following eight, and the period ends the header. In the canonical zero-based Gematria Primus order the nine cipher indices are **24, 19, 21, 23, 27, 2, 14, 10, 19**. The index labels A, I and O are **24, 10 and 3**. A single primer `k` ranges over all 29 indices; each first-rune crib picks one primer, so the six displayed rows are not an open-ended key search.

For ciphertext feedback, `P[0] = C[0] − k` and `P[i] = C[i] − C[i−1]`. For plaintext feedback, `P[0] = C[0] − k` and `P[i] = C[i] − P[i−1]`. All subtraction is modulo 29. Neither rule resets at the word separator, line break or page edge. The complete run processes **all 232 runes on LP2-54**, not just the header. Punctuation is retained in the source but has no arithmetic slot.

The [frozen plan](experiments/records/lp2-54-header-feedback/plan.json) names the source-discussion hash, transcription hash, alphabet and exact bounds. The [full result](experiments/records/lp2-54-header-feedback/results.json) contains all **58** mode-and-primer combinations, including each full 232-rune output. The producer checks that re-encryption returns every original rune; an independent checker verifies the equations at every position.

## Header outputs

![The nine source positions above six fixed-rule outputs, with the separator after the first rune.](experiments/records/lp2-54-header-feedback/header-feedback.svg)

[Open the comparison at full size](experiments/records/lp2-54-header-feedback/header-feedback.svg).

| Feedback | First-rune crib | Primer | Nine output labels, separated after rune one |
| --- | --- | ---: | --- |
| Ciphertext | A | 0 | A · A TH TH R R EO AE N |
| Ciphertext | I | 14 | I · A TH TH R R EO AE N |
| Ciphertext | O | 21 | O · A TH TH R R EO AE N |
| Plaintext | A | 0 | A · A Y Y U U P Y OE |
| Plaintext | I | 14 | I · N EO J T S EA J H |
| Plaintext | O | 21 | O · T C/K E N OE NG E U |

The ciphertext-feedback second word is the **same for all 29 primers**, because every position after the first subtracts two known cipher runes. Choosing A, I or O therefore changes only the first rune in that model. Plaintext feedback propagates the primer choice through later positions. This is why confusing the two clocks can produce a different purported header reading.

These rune-label strings are transparent outputs, not established English or a scored decryption. Even an apparent word from a larger search would require the complete search budget, a fixed word list and transliteration, a known-reading control, and an untouched continuation. An extra encryption layer, alphabet permutation, different lag, interruption rule or manually chosen function could change every output. None is tested here.

## Reproduce

From a checkout or the [downloadable bundle](downloads/experiments/lp2-54-header-feedback.zip):

```text
python experiments/records/lp2-54-header-feedback/run.py --check
python experiments/records/lp2-54-header-feedback/check.py
python experiments/records/lp2-54-header-feedback/plot.py --check
```

No external service or Python package is needed. The run was not altered after inspecting output. This census **does not support a header reading by these six simple fixed-rule candidates**, but it does not rule out the broad autokey family or the original proposal’s other, unspecified C/K/D functions. The related [LP2-54–55 interruption tests](#/experiments/lp2-54-55-autokey-reset) ask a separate periodicity question and should not be counted as independent confirmation of this header test.
