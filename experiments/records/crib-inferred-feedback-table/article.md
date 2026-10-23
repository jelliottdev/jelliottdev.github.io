# How much can an opening fix in a feedback table?

**Question.** Suppose a cipher has an arbitrary, unknown table with one output for each of the 29 rune indices. If we propose a twelve-rune opening on an LP2 page, how many entries of that table does the opening actually determine?

**Result.** With the previous **ciphertext** rune as feedback, 31 of 495 fixed page-and-opening pairs give internally consistent table assignments. Each fixes only ten or eleven of 29 entries, leaving **29¹⁹ or 29¹⁸** different complete tables. With the previous **plaintext** rune as feedback, just one of 495 pairs is internally consistent; it fixes nine entries and leaves **29²⁰** complete tables. These are algebraic fits to proposed openings, **not decryptions**.

![Nine constrained entries and twenty free entries in one compatible case.](experiments/records/crib-inferred-feedback-table/table-constraints.svg)

## The rule and what an opening can tell us

For each rune after the first, the ciphertext-feedback rule is **Pᵢ = Cᵢ − f(Cᵢ₋₁) mod 29**. The plaintext-feedback variant uses **f(Pᵢ₋₁)** instead. Once a proposed plaintext is supplied, each position makes one demand of the form “table entry *x* must equal *y*.” Repeated demands on the same input must agree. A contradiction rejects that exact opening under that exact rule; a consistent set of *r* inputs leaves **29^(29−r)** ways to fill the remaining table. The first proposed plaintext rune needs an external primer or rule and supplies no table constraint here.

To see whether a compatible opening carries information beyond itself, we inspected the **next twelve ciphertext positions** without using any proposed continuation. For the 31 consistent ciphertext-feedback pairs, only **two, four, or five** of those twelve positions have a previously assigned table input; the rest need free entries. The sole consistent plaintext-feedback pair predicts one next symbol before its next table input is undefined. These are counts of determined positions, not checks against a known later plaintext. No continuation is presented as a reading.

## Scope and checks

The census uses the first 24 runes, including headings, of **LP2-00–55 except runeless LP2-50**, and the same nine fixed twelve-rune openings used in the earlier opening tests. Each page is treated separately, with canonical Gematria Primus indices modulo 29. It does not choose a primer, score English, test other openings, or claim the manuscript uses either feedback rule.

Run `python experiments/records/crib-inferred-feedback-table/run.py --check` and `python experiments/records/crib-inferred-feedback-table/check.py` from the repository root. The independent checker reads page JSON instead of the text input used by the producer, reconstructs the constraints with value sets, checks all 990 cases and their forward-coverage counts, and confirms the table-count theorem by enumerating **all 27 functions over F₃ and 3,125 functions over F₅** in planted and adversarial controls. `results.json` retains the case-by-case scope, conflicts, assigned entries, compatible-table count, and forward coverage.
