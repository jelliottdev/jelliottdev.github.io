# Rotating and folded wordlist keys

Can the 43 archived keys recover a familiar 12-rune opening if each key changes shape as it repeats?

## Finding

**No exact opening match.** We tested **6,272 key schedules** at every phase of their actual repeating cycles on the 55 rune-bearing unsolved pages. Their **3,104,640 comparisons** with nine fixed known-reading openings produced zero exact matches. The closest opening agreed for four runes. This is a narrow exclusion of the stated keys, schedules, positions and target readings; it does not judge other plaintext openings.

![For key-01, left rotation changes the next nine-rune cycle; folding walks back through key positions.](experiments/records/rotating-folded-key-openings/clock.svg)

The diagram shows the *key position* used at each of the first 12 ciphertext runes for the first archived key. A left rotation uses slots 0–8 once, then begins the next cycle at slot 1. Folding goes forward and then back. We also tested right rotation and a fold that does not repeat either end. For each key, we reduced identical repeated cycles to their true period before testing every phase. The result file separates **6,272 declared settings** from duplicated 12-step clocks; variants are counted independently because they specify different rules.

## Scope and reproduction

The key list is the 43-rune-key list pinned in the [public wordlist replay](#/experiments/public-wordlist-vigenere). Each page starts its own clock. Non-rune marks do not advance it; each output is the ciphertext rune index minus the scheduled key index modulo 29. We compare only the first 12 runes with the nine openings selected before this test. The original public attempt used ordinary repeating keys; **these rotating and folded schedules are new tests here**, not a claimed historical replay. They do not test other keys, shifts, word resets, interruptions or a language score.

The [manifest](experiments/suites/classical-key-schedules/manifest.json) fixes the schedules and inputs. [Results](experiments/records/rotating-folded-key-openings/results.json) retain per-variant totals, planted recovery controls and a digest of every decoded page start. From the repository root, run `python experiments/records/rotating-folded-key-openings/run.py --check` and `python experiments/suites/classical-key-schedules/check.py rotating-folded-key-openings`. The independent checker rebuilds runes from page JSON and computes the schedules separately.
