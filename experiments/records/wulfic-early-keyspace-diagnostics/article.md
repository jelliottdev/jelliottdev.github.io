# Four early keyspace checks on LP2

**Finding.** The pinned Wulfic source tests pass, but none of their four specified models identifies a reading. Two frequency models disagree with LP2 under their fixed −10-nat rule. Two lag scans find no value past their multiple-test thresholds. These are checks of particular statistical predictions, not a search of all possible keys.

![Four distinct Wulfic keyspace checks and their nearest results against source decision lines.](experiments/records/wulfic-early-keyspace-diagnostics/comparison.svg)

| Source claim | What is actually measured | Result |
| --- | --- | --- |
| **C10 · English-like running key** | Pooled rune frequencies for three key-value mappings, three arithmetic directions, three mixtures of solved-text and uniform key letters, and 29 offsets | Best log-likelihood ratio **−14.38**, below the source's −10 exclusion line |
| **C13 · small key alphabets** | Pooled frequencies for uniformly chosen decimal digits, hex digits, Latin A–Z, or source English letter weights; three directions and 29 offsets | Best ratio **−14.27**, below −10 |
| **C11 · ciphertext autokey** | A 29-bin combination of ciphertext runes separated by each lag 2–1000, both signs, within the source's nine sections | Smallest unadjusted **p = 0.000559** at lag 880; above the corrected **0.00000501** pass line |
| **C12 · ciphertext-selected alphabet** | Off-diagonal rune transitions at each lag 1–1000, within those sections | Smallest approximate **p = 0.003916** at lag 142; above **0.00001** |

The source's thirteen test assertions all pass, including synthetic encryptions that the four diagnostics detect and a random-stream calibration for C12. An independent checker recalculates **all 27 C10, 1,998 C11, 1,000 C12 and four C13 manuscript rows** from the preserved numerical inputs. It also confirms that the source's 12,956 GP29 rune values are exactly the sequence in Liberpedia's LP2-00–55 page records.

## What the findings mean

The C10 and C13 scores compare *one-rune frequencies* with a model based on solved LP1 text. They depend on the assumed independence of plaintext and key values and the stated key-letter distributions. They do not test every English passage as a running key. C13's wider base-60, two-digit and byte alphabets have too little predicted signal for this same frequency check; the source explicitly marks them **untestable by this criterion**, not excluded.

C11 tests the frequency pattern expected from a particular additive ciphertext-feedback relation. C12 tests a distinct transition pattern expected when a prior ciphertext rune selects one of 29 substitution alphabets. Neither test tries to decrypt LP2 or excludes arbitrary feedback or alphabet-selection rules. Their smallest raw p-values must be compared with the source's thresholds across the full lag search, not read as individual discoveries. The later [AC/AD lag study](#/experiments/wulfic-lag-reuse-models) tests different pair laws and stretch scores; it does not replace these source checks.

## Reproduce

The [plan](experiments/records/wulfic-early-keyspace-diagnostics/plan.json) fixes the model grid and decision lines. [Inputs](experiments/records/wulfic-early-keyspace-diagnostics/inputs.json) preserve the source-derived rune stream, section boundaries and solved-text model; [results](experiments/records/wulfic-early-keyspace-diagnostics/results.json) include every manuscript statistic. Run the independent calculation with:

```text
python experiments/records/wulfic-early-keyspace-diagnostics/check.py
python experiments/records/wulfic-early-keyspace-diagnostics/plot.py --check
```

To rerun the **unchanged pinned source tests** and rebuild the data bundle, use a checkout of [Wulfic's repository at this revision](https://github.com/Wulfic/Cicada3301-Liber_Primus/tree/bf89d3d13aad2b8f2c95ab195cf1b092f250775c):

```text
python experiments/records/wulfic-early-keyspace-diagnostics/replay_source.py --source PATH_TO_CHECKOUT
```

The source test is [`tests/test_keyspace.py`](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tests/test_keyspace.py). The model arithmetic is in [`tools/lpcore/stats.py`](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/lpcore/stats.py). The replay uses the source's nine section boundaries; those are not individual page resets. Other transcriptions, plaintext priors, nonadditive rules and later cipher layers are outside these tests.
