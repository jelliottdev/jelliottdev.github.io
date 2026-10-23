## Finding

The proposed cumulative rule has no adjustable key: it turns into a difference between neighboring ciphertext runes. Applied separately to every nonempty page of LP2-00–55, its **12,956 output runes remain nearly flat**. Their index of coincidence is **0.035319**, close to the raw LP2 stream's **0.034478** and far below the **0.061139** measured from the site's 2,797 decoded LP1 runes. That comparison does not prove LP2 uses English or the same spelling conventions as LP1, but it supplies no positive reading under the literal rule.

![F-rune rates for the literal output, solved LP1 readings and raw LP2 ciphertext.](experiments/records/cumulative-autokey-literal/f-rate.svg)

The output has **88 F runes (0.68%)**. This number is forced by **86 repeated adjacent ciphertext runes** plus the first rune of each of two pages. The LP1 reading control has **44 F runes among 2,797 (1.57%)**. The chart is descriptive: the corpora differ in length, topic and cipher history.

## Rule tested

The reported formula is `P[k] = C[k] − sum(P[0] ... P[k−1]) mod 29`. We start the sum at zero at the beginning of each page. It follows algebraically that `P[0] = C[0]` and `P[k] = C[k] − C[k−1] mod 29` afterward. The program also re-sums every output prefix and verifies that it reconstructs the exact input rune. This is the literal formula, not a search for primers or a plaintext-feedback Fibonacci recurrence.

## How to reproduce

From the repository root, run `python experiments/records/cumulative-autokey-literal/run.py --check`. The saved [29-value distributions and per-page first-rune ledger](experiments/records/cumulative-autokey-literal/results.json) include hashes for every transcription and reading file used.

This result covers page-local starts and the archived 29-rune transcription. A rule that carries state between pages, skips a rune, adds another key layer, or changes its alphabet is a different test. The known LP1 readings serve only as a transparent comparison, not a formal null distribution for every possible plaintext.
