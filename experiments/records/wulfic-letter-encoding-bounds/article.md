# Can simple letter-encoding rules explain LP2?

Two precise proposals make predictions about the visible runes. We replayed both from the [pinned source tests](https://github.com/Wulfic/Cicada3301-Liber_Primus/tree/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tests) and independently rebuilt their manuscript measurements. **Neither rule fits under its stated assumptions.** This does not rule out other ways to handle repeated runes or homophones.

![Two checks: 29 possible repeat markers narrow to three by count and zero by word position; the best dedicated-homophone model predicts a frequency mismatch far above the observed one.](experiments/records/wulfic-letter-encoding-bounds/comparison.svg)

## A repeated rune as a marker

In the first proposal, one chosen plaintext rune makes the ciphertext repeat its previous rune. If that rule operates throughout LP2, the *number* and *positions* of visible repeats should resemble occurrences of that plaintext rune. We tested each of the 29 possible markers. Only **NG, IA and EA** survive the source's repeat-count test. None fits the source's word-position test: their scores are −106.4, −149.4 and −67.7, respectively, against its −10 decision line. Thus the proposed marker rule has no surviving rune in this fixed model.

This relies on solved-page rune frequencies and word positions representing the unknown plaintext, and on a nonzero multiplier in the proposed recurrence. A different rule for avoiding or generating repeats would need its own test.

## One-to-many letters with fixed choices

The second proposal gives each plaintext rune its own dedicated set of ciphertext runes, with equal use of the choices within that set. We gave the model every allocation of the 29 available ciphertext symbols across the 26 plaintext rune types seen in the solved sample. Even the **best allocation predicts a frequency mismatch of 4,802** on the source's chi-square scale. The actual LP2 rune counts score **26**. The source's cutoff for this model is 200.

The best allocation gives O two ciphertext symbols and E three; the other used plaintext runes get one each. This is an expected-frequency bound, not an attempted decryption. Unequal choices, context-dependent homophones, extra cipher layers or a different plaintext distribution are outside this result.

## What we checked

The reconstructed sample has 2,901 known plaintext runes. LP2-00–55 has 12,956 runes, with 86 repeats in 12,947 within-section adjacent opportunities. The original six targeted source tests pass, including planted marker examples. An independent calculation checks the count and position tests, and a separate dynamic program checks the optimal homophone allocation. Source and site measurements agree at the decision points.

To check the saved result and figure, run `python experiments/records/wulfic-letter-encoding-bounds/check.py` and `python experiments/records/wulfic-letter-encoding-bounds/plot.py --check`. The [record files](experiments/records/wulfic-letter-encoding-bounds/plan.json) state exact bounds and source revisions. The original source replay additionally needs the pinned external repository.
