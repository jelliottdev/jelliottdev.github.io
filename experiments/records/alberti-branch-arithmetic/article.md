# What does the reported Alberti branch arithmetic establish?

The [Alberti-disk proposal](#/wiki/reported-attempts?section=alberti-disk-branches) combines movable alphabets, four rule transitions, a repeating shift sequence and branches at punctuation. Its LP2-39 reading would require **all** of those pieces. The supplied discussion refers to separate method files and diagrams, but the text available for this audit does not fix the complete disk alphabets and transition rules. We therefore tested two narrower claims that can be checked directly: the identified LP2-39 row and the later 4–5–4 shift arithmetic. **This is not a replay of the proposed decryption.**

![Four cards show the source row's 19 runes, the reproducing left and right raw shift totals, and the right totals' different modulo-31 residues.](experiments/records/alberti-branch-arithmetic/summary.svg)

## What matches

The specified second-section row of [LP2-39](#/page/lp2-39) is present in the archived transcription. It has **19 runes** in five pieces of **3, 4, 6, 5 and 1**, separated by one full stop and three hyphens. The discussion represents these boundaries with other marks in its display; the rune groups are the same. The marks can define *candidate* branch points, but their presence does not tell us what disk state to inherit or which branches to read.

The source also supplies thirteen signed numbers for each of two plant readings, a four-number overlay `−5, −6, −3, −11`, and final arrays split into groups of 4, 5 and 4. All four **raw short-group sums** reproduce:

| Sequence | First four plus overlay | Last four plus overlay | Posted raw totals |
| --- | ---: | ---: | --- |
| Left | −13 | −17 | −13, −17 |
| Right | −33 | −39 | −33, −39 |

The posted final arrays also total **−13, −15, −17** on the left and **−33, −15, −39** on the right. The middle-group −15 is therefore an arithmetic property of those supplied arrays. It does not independently verify that the plant was counted correctly, that the grouping was fixed before the matching words were selected, or that these shifts decode a page.

## The modulo sign matters

The source next writes the right short totals as `−33 ≡ +2` and `−39 ≡ +8` modulo 31. Under ordinary modulo arithmetic, they are **−2 ≡ 29** and **−8 ≡ 23**. The stated positive **2** and **8** are the *opposite* residues. A mirror operation might deliberately reverse direction, but that would be an additional sign-conversion rule; it does not follow from reduction modulo 31 alone. The source's disk alphabets and direction convention are needed to check that separate step.

As an alignment-sensitivity check, the script also rotates each fixed thirteen-number plant sequence through all **13** starting positions, keeping the same 4–5–4 grouping and overlay. The left ordered raw target `−13, −17` occurs at its posted start only. None of the right rotations gives the posted **positive** residue pair `2, 8` under ordinary modulo 31. These 13 rotations are a limited diagnostic, **not** a random null or a probability of the whole proposal: the source explored other disk sizes, mirror models, shifts, branches and readings.

## What remains untested

The candidate words on LP2-39 are assembled across output branches after disk changes. The text we have does not provide a complete frozen machine-readable transition table, both disk alphabets for every variant, the branch inheritance rule, or a rule for selecting and assembling final letters. We cannot infer those missing rules from an appealing output. In particular, this audit neither confirms nor excludes an Alberti-style cipher, and it does not attach a probability to the reported names or words.

To test the reading, pin one version of the source model, execute **every branch** of this row, save all unedited output and word-selection decisions, and run the same search on solved-page and matched control inputs. The [plan](experiments/records/alberti-branch-arithmetic/plan.json) and [results](experiments/records/alberti-branch-arithmetic/results.json) preserve exactly the narrower checks done here.

From the repository or extracted experiment bundle, run:

```text
python experiments/records/alberti-branch-arithmetic/run.py --check
python experiments/records/alberti-branch-arithmetic/check.py
```

Both scripts use the Python standard library. The checker independently recounts the row, recalculates the posted arrays and residues, and repeats all 26 rotated short-group calculations without importing the producer.
