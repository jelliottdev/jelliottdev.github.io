## What the source's language test can establish

An archived search scored possible Liber Primus readings with models for Latin, Greek, Old English and Enochian. Before using those models on the manuscript, its [frozen plan](experiments/records/dukotah-nonenglish-control-gate/source-PREREG.md) set a control: **a language model had to find planted text more often than the English scorer did.**

The saved controls show a tie. For **each of the four languages**, both scorers beat their own wrong-key threshold on **all 24 planted passages**. The language models worked on these plants, but they did not beat English by the plan's chosen measure. **Zero of four models passed the frozen strict-comparison rule.**

![Both scorers succeed on all 24 planted passages for each of four languages.](experiments/records/dukotah-nonenglish-control-gate/control-gate.svg)

The [control program](experiments/records/dukotah-nonenglish-control-gate/source-control.py) used a different comparison: how far each scorer's median sits above its wrong-key scores, measured in standard deviations. On that measure, all four language models beat English. That may be a useful diagnostic, but the frozen plan did not name it as the pass rule. The program marked all four models as validated and continued.

The source [reports](experiments/records/dukotah-nonenglish-control-gate/source-results.json) 20,480 manuscript decodes and zero candidates above its final bar. **We did not rerun that grid here.** This audit checks the saved control rows and the source's decision logic. It shows that the reported zero is **not a control-validated exclusion under the original rule**. It does not show a non-English plaintext or refute the source's individual score calculations.

The English scorer's perfect showing on these particular plants also limits what the control could reveal: a harder, predeclared set of passages would be needed to measure an advantage in *detection rate*. The source's vowel-dropped English control does show English losing to its own-model score, but vowel-dropped English is not one of the four non-English registers tested here.

## Check it

Run `python experiments/records/dukotah-nonenglish-control-gate/check.py` and `python experiments/records/dukotah-nonenglish-control-gate/plot.py --check` from the repository root. The checker hashes the pinned source files, reads every saved control row, and applies both the frozen power comparison and the program's later comparison. The source used 24 plants and 60 wrong-key controls per register. The full source scripts, plan, saved control output and reported manuscript summary are bundled with this record under the source repository's MIT license.

A follow-up would freeze a control that separates English from the other languages before looking at manuscript scores, then measure its power and calibrate the complete search against the same decision rule. That would test whether this bounded key-and-language search can detect the kind of reading it claims to exclude.
