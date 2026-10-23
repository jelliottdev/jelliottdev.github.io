# Mirror and alternating-group scores in the saved interrupt database

The [pinned LiberPrayground source](https://github.com/relikd/LiberPrayground/blob/719380ebee0523ad7f2fbf389c6f960d51bea5a4/LP/InterruptDB.py) stores candidate ways to omit `ᚠ` or `ᛠ` runes and then group what remains. One group rule mirrors a repeating key position; two others alternate positions in pairs or threes, differing in whether the chosen runes are removed before or after that split. **A high score means the groups have striking rune frequencies. It does not reveal a key or words.**

![Known-period detection: mirror 4/4, remove then split 10/10, split then remove 8/10.](experiments/records/relikd-interrupt-pattern-database/control.svg)

On a 600-rune known reading encrypted with a five-position pattern, the correct period scored above periods 2–8 in **22 of 24** source-rule controls. The two misses both use the “split, then remove” rule with the source's normal-frequency score. A separately labeled **post-result** check shuffled the same planted ciphertext values, kept the inserted `ᚠ` positions fixed and repeated the period search 49 times. The planted score beat every shuffled maximum in 19 of 24 arms; five had at least one shuffled result as high. These are checks of the score's ability to find a *known* pattern. We supplied the interrupt positions, so they do not show that the method can discover interruptions in LP2.

We then recounted **all 7,407 rows** in the 24 committed mirror/modulo database files. Every score agrees with the pinned source calculation to the displayed five-decimal rounding (absolute difference at most 0.000005). This verifies the saved arithmetic and the source-to-site rune streams, not how the database's best skip sets were originally selected. Across its nine sections, **44 complete LP2 pages and parts of seven more** contribute at least one rune to a saved score; five other pages were verified against the source but entered no saved score. The [exact page coverage](experiments/records/relikd-interrupt-pattern-database/coverage.json) and [all row results](experiments/records/relikd-interrupt-pattern-database/results.json) are available for inspection.

**No reading follows from the saved high scores.** The source selected over many skip sets and periods, and we did not repeat that expensive selection on shuffled LP2 pages. Comparing its best saved score with a fixed-rule random baseline would make chance patterns look more convincing. The positive controls establish only structural period detection under a supplied skip mask; they are not a complete-message decryption test. Two source-rule controls failed even that narrower gate. The saved files are evidence of candidate data, without an independently recovered execution log proving every historical search ran as documented.

The [base plan](experiments/records/relikd-interrupt-pattern-database/plan.json) fixes all 24 source files and the row recount. The [shuffle addendum](experiments/records/relikd-interrupt-pattern-database/shuffle-plan.json) was frozen after the LP2 row scores were inspected and must be read as a control-power diagnostic, not prior statistical confirmation. To reproduce, obtain the pinned Git revision `719380ebee0523ad7f2fbf389c6f960d51bea5a4` separately. These scripts hash-check its Git blobs and do not redistribute the source:

```text
python -X utf8 experiments/records/relikd-interrupt-pattern-database/control.py --source-root SOURCE --check
python -X utf8 experiments/records/relikd-interrupt-pattern-database/target.py --source-root SOURCE --check
python -X utf8 experiments/records/relikd-interrupt-pattern-database/shuffle.py --source-root SOURCE --check
python -X utf8 experiments/records/relikd-interrupt-pattern-database/coverage.py --source-root SOURCE --check
python -X utf8 experiments/records/relikd-interrupt-pattern-database/check.py --source-root SOURCE
python experiments/records/relikd-interrupt-pattern-database/plot.py --check
```
