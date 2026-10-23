# Does rune equality reveal a repeating alphabet?

If an encryption alphabet repeats every **L** runes, the same alphabet acts on positions `i` and `i+L`. A one-to-one alphabet preserves whether those two plaintext runes are equal. Wulfic's Stage AE uses that invariant to check **every possible lag from 11 to 12,945** in the joined unsolved LP2 text. This is a way to test a whole family of periodic substitutions without guessing the alphabets themselves.

**Result:** the source's controlled rule excludes **10,030 of 12,935 periods**, including 1033, 1729 and 3301. It leaves **2,905 periods open**. No period has the excess equality required for a positive detection. An open period is not evidence that it is the key length.

![Observed LP2 rune equality versus the lowest planted periodic-alphabet rate at periods 1033, 1729 and 3301](experiments/records/wulfic-periodic-alphabet-lags/comparison.svg)

| Repeating period | LP2 equal rune pairs | LP2 rate | Lowest planted-control rate | Source verdict |
| --- | ---: | ---: | ---: | --- |
| 1033 | 422 / 11,923 | 3.54% | 5.65% | Excluded |
| 1729 | 407 / 11,227 | 3.63% | 5.20% | Excluded |
| 3301 | 326 / 9,655 | 3.38% | 5.69% | Excluded |

The figure shows *rates* for three named periods. The actual decision uses a binomial tail, not a simple line at 5%. The [complete source table](experiments/records/wulfic-periodic-alphabet-lags/source-stage_ae_lags.tsv) has the pair count, equality count, rates and verdict for every tested lag.

## What the comparison means

The source assumes a periodic key selecting a fixed, **bijective** rune alphabet at each residue position. At the correct period, equal ciphertext pairs then occur exactly where plaintext pairs are equal, before any other processing. The model allows the observed anti-doublet tendency by redrawing 81% of adjacent repeat collisions in its simulated streams. Its lower-bound test asks whether the observed equality count is unusually small if the plaintext's agreement probability is at least 5%.

The source generated 20 flat-rune null streams and 100 periodic-alphabet positive controls: ten each from Emerson prose and solved LP1 at periods 1033, 1729, 3301, 6000 and 9000. None of the 20 null streams triggered its positive rule. **All 100 positive controls passed and none was excluded** at its planted period. The full source run reported valid. This establishes that its chosen controls can distinguish these planted cases; it does not prove that every natural-language text or every periodic cipher has the same agreement rate.

The exclusion count is conditional on the source's English/LP1 control sources, 5% minimum-agreement assumption, binomial model and archived transcription. Lag pairs share rune positions, so the binomial tail is a model-based score rather than an exact independent-trial probability. The per-lag exclusion threshold is not a correction for selecting among all 12,935 periods. A changing alphabet, non-bijective mapping, running state, word reset or additional transformation may break the equality invariant. These cases remain outside the test.

## Reproduce

The two bundled tables were regenerated from the unmodified [pinned Stage AE program](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_ae.py) at commit `bf89d3d`; both match that revision's output byte-for-byte. From the extracted Liberpedia repository, Python's standard library verifies the bundle and independently recounts all 12,935 lag agreements from the 56 page text files:

```text
python experiments/records/wulfic-periodic-alphabet-lags/run.py --check
python experiments/records/wulfic-periodic-alphabet-lags/check.py
python experiments/records/wulfic-periodic-alphabet-lags/plot.py --check
```

The independent checker builds a bitset for each rune, counts matches at every lag, verifies the three named lower-tail probabilities, and checks a planted periodic alphabet that must preserve equality. The [plan](experiments/records/wulfic-periodic-alphabet-lags/plan.json) pins all manuscript inputs and source revision. The optional `replay_source.py` reruns the original program from a matching checkout; it requires that repository and its NumPy dependency. Wulfic's Stages AC and AD explore related lagged-key ideas, but their pinned `--quick` runs fail in a shared control-array shape operation before LP2 scoring. This record does not present their historical outputs as reproduced.
