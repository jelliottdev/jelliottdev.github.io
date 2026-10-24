Two archived searches each report 20,480 Liber Primus decodes and no surviving candidate. Each set a positive-control rule before searching: its proposed scorer had to detect planted text **more often than the English scorer** when each was compared with its own wrong-key controls. Neither saved control meets that rule. Both programs used a different comparison to continue.

**Four language models.** The [frozen plan](experiments/records/dukotah-nonenglish-control-gate/source-PREREG.md) tests Latin, Greek, Old English and Enochian models. **Zero of four** beat English on detection rate: both scorers find all 24 plants in every language. The program instead uses a standardized-score difference (*d-prime*) and passes all four.

**Matched rune spelling.** A [separate plan](experiments/records/dukotah-nonenglish-control-gate/sibling-matched/source-PREREG.md) tests an **English** quadgram scorer adjusted for rune spelling. **Zero of three** eligible controls beat ordinary English against each scorer’s own wrong-key maximum. Latin and Greek are 24/24 under both; vowel-dropped English is 0/24 under both. The program also checks a fixed −5.5 score bar. At that bar, Latin rises from 12/24 to 19/24, so the program passes it through an OR condition.

![The four language-model controls tie English on every planted passage.](experiments/records/dukotah-nonenglish-control-gate/control-gate.svg)

The two tests answer different questions. The first uses models trained for other languages. The second changes how an English model handles rune spelling; its improvement at a fixed bar does **not** turn it into a Latin or Greek language model. The saved rates show no advantage under either test’s frozen *own-null detection-rate* rule. The changed comparisons may be useful diagnostics, but they were not the declared pass criteria.

The original [language-model program](experiments/records/dukotah-nonenglish-control-gate/source-control.py) uses d-prime to mark four registers validated. The separate [matched-runic program](experiments/records/dukotah-nonenglish-control-gate/sibling-matched/source-control.py) uses the own-null result **or** a fixed-bar result, marking Latin validated. These are checks of the pinned plans, source decisions and saved control rows. **We did not rerun either planted simulation or either 20,480-case manuscript search.** Their reported zero survivors therefore cannot be presented as exclusions validated under their original control rules. The audits do not establish what language, if any, the unsolved pages contain.

## Check the controls

From the repository root, run:

```bash
python experiments/records/dukotah-nonenglish-control-gate/check.py
python experiments/records/dukotah-nonenglish-control-gate/sibling-matched/check.py --check
```

The first checker compares all four saved language-model rows with both decision rules. The second verifies the pinned sibling source bytes and recomputes the frozen and executed decisions for Latin, Greek and vowel-dropped English. Source plans, code and saved receipts are bundled under the source repository’s MIT license. A new search would need a predeclared control that can reveal a detection-rate advantage, followed by one unchanged decision rule and a matched null for the full search.

## Saved results

The [saved language-model controls](experiments/records/dukotah-nonenglish-control-gate/source-out_control.json), [language-model audit](experiments/records/dukotah-nonenglish-control-gate/results.json) and [matched-rune audit](experiments/records/dukotah-nonenglish-control-gate/sibling-matched/results.json) support rechecking the frozen and executed gate decisions without repeating the original simulations. They preserve aggregate control summaries and audit receipts, not all original trial outputs. Neither reported 20,480-case manuscript search was locally rerun, so these materials do not validate its zero survivors under the frozen control rule.
