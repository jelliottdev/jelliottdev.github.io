# Homophonic search: synthetic recovery controls

The search did not completely recover any of three known synthetic class streams. All three also missed both source detection gates. This is a failed control check, not evidence that Liber Primus excludes homophonic substitution: no manuscript target was scored.

![Both detection measures remain below their source gate](experiments/records/dukotah-homophonic-recovery-control/control-gates.svg)

The idea is to group the 29 rune values into fewer underlying classes, allowing several runes to stand for the same class. We ran unchanged functions from Dukotah’s recovered campaign-15 P6 program on three planted inputs, each 12,956 symbols long: two with 12 classes and one with 18. Two plants suppress repeated letters using the source rule; the other does not. The frozen search uses 4,000 iterations and four restarts per fit. This tests one recovered implementation, not every search proposed in campaign-14 D-03.

The program’s class-alignment measure reached 57–62%, but it lets multiple true classes match one output class. A one-to-one alignment reached only 37–56%; none was complete recovery. The search-score detection z values were 1.19–1.89 and held-out values 0.21–1.94, all below the required value greater than 3. These two evaluations reuse the same three plants and are not independent trials.

Each plant also received eight shuffled fits with the same four-restart budget. Seven, two and one of these respectively scored at least as highly as the planted fit. Eight comparisons cannot establish the original proposal’s 1,000-shuffle envelope or a general false-positive rate. The source detection calculation itself uses unequal restart budgets; we preserve that rule and report the equal-budget comparison separately.

There are additional reasons to keep the conclusion narrow. The source returns the best final restart rather than the best state visited. It uses trigrams at 12 classes and bigrams at 18, whereas D-03 proposed a broader multilingual quadgram search. The selected main-tree training files mix puzzle material, notes and key lists; they are not independent clean English prose. The recovered subtree lacks its training inputs, so this is an explicitly chosen input reconstruction, not a verified historical replay. Original D-03’s remaining target search, languages, structured-data possibilities and held-out design remain unresolved.

## Inspect and reproduce

The [frozen plan](controls-plan-frozen.json), [complete results](controls-results.json), [independent checks](independent-check.json) and [input contract](external-input-contract.json) retain the exact choices. The checker separately reconstructs plants and models and rescores returned maps, 1,500 held-out shuffle scores and all 24 equal-budget shuffled-fit witnesses. The 72 source unequal-budget null-fit witnesses and three single-shuffle maps were not retained; their aggregate moments remain producer summaries.

Python 3.12.10 with NumPy 2.5.4 reproduced the deterministic outputs in a fresh directory in about 40 seconds. From the extracted bundle root, with the pinned source repository available locally, run:

```text
python experiments/records/dukotah-homophonic-recovery-control/replay_controls.py --from-git /path/to/cicada3301 --workdir /private/new-replay
```

Alternatively prepare exact external files first and use `--inputs /private/prepared-inputs`. [Preparation instructions](PORTABILITY.md) describe the four fixed paths and hashes and an explicit optional download mode. Training texts are not bundled. The replay compares every deterministic output exactly, ignores only durations and the resulting raw-report hash, and never overwrites expectations.

The recovered code and documentation are by Dukotah at revision `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`; the exact [source license](source/LICENSE) grants MIT terms for original work and explicitly excludes puzzle artifacts and third-party/community transcriptions. The original [D-03 proposal](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/campaign14/REDTEAM-PROPOSALS.md) and recovered P6 source are included with attribution. The separate [language-control audit](#/experiments/dukotah-nonenglish-control-gate) addresses different searches and is not this rerun.
