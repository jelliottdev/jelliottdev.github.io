# A bounded test of the P20 boundary model

**Question.** In a published P20 analysis, do the supplied numeric boundary states support a single *static affine* rule over the finite field modulo 83?

**Result.** The source's finite calculation reproduces, including its independent check and planted controls. Across **34,020** allowed assignments of state pairs at eight boundary contexts, **six** stated lower-complexity combinations have **no** complete fit. The saturated six-feature/six-feature combination has **five** fits. That count is ordinary under the source's exact conditioned comparison: **4.94** fits expected, with probability **0.552** of five or more. It does not identify a boundary transform or decode a page.

![Eight supplied boundary contexts yield no fit in six lower-complexity static classes; five saturated fits are near the exact null expectation.](experiments/records/public-p20-static-boundary/boundary-fit.svg)

## What the finite test actually says

The [pinned repository](https://github.com/emmanuel6474/liber-primus-p20-analysis/tree/a39e7de90ff9414791fe5f4f8d44540bd0bdb089) describes an **812-rune section it calls P20**. Its bundled numeric file gives eight chosen boundary contexts, six numeric features per context and a menu of permissible pairs of state values. Choosing one pair from each menu gives 34,020 assignments. A proposed *static affine* rule would express each of the two output state coordinates as a fixed linear combination of selected features plus a constant, all modulo 83. The scripts test the declared feature-count pairs `(4,4)`, `(4,5)`, `(5,4)`, `(5,5)`, `(5,6)`, `(6,5)` and `(6,6)` against all eight contexts.

The zeros are exact **within those eight supplied menus and model classes**. The five `(6,6)` fits use all six features for each coordinate plus an intercept. The source separately asks whether the held-out c18 menu’s five fits distinguish it from alternatives. Its independent exact finite-population calculation finds the observed count unexceptional. Two planted low-complexity affine laws are recovered exactly, while one-value mutations break them. These controls show the fitter can recover simple laws when they are present in synthetic data.

We ran the source's [complete cross-validation](https://github.com/emmanuel6474/liber-primus-p20-analysis/blob/a39e7de90ff9414791fe5f4f8d44540bd0bdb089/analysis/33_boundary_complete_crossvalidation.py), [independent exact-null verifier](https://github.com/emmanuel6474/liber-primus-p20-analysis/blob/a39e7de90ff9414791fe5f4f8d44540bd0bdb089/analysis/35_exact_null_independent_verifier.py), and [plant-and-recover control](https://github.com/emmanuel6474/liber-primus-p20-analysis/blob/a39e7de90ff9414791fe5f4f8d44540bd0bdb089/analysis/38_positive_control_plant_and_recover.py) from pinned Git blobs in a temporary directory. Each passed and regenerated a JSON object identical to its committed result. Liberpedia's separate checker recomputes the 34,020 menu product and the exact probability from the saved weight histogram.

The repository calls itself **partial** and [says the original raw workspace is missing](https://github.com/emmanuel6474/liber-primus-p20-analysis/blob/a39e7de90ff9414791fe5f4f8d44540bd0bdb089/PROVENANCE.md). This test **does not independently derive its eight state menus or six features from the manuscript**. It cannot rule out a dynamic or different boundary rule. Its “P20” is the source's section label; this record does not equate it to one Liberpedia page.

## Reproduce from the pinned source

The pinned Git tree has no explicit license, so the experiment ZIP contains our harness, plan and results, **not** copies of the source code or normalized numeric input. Clone the [source repository](https://github.com/emmanuel6474/liber-primus-p20-analysis/tree/a39e7de90ff9414791fe5f4f8d44540bd0bdb089), check out commit `a39e7de90ff9414791fe5f4f8d44540bd0bdb089`, then from the Liberpedia repository root run:

```text
python experiments/records/public-p20-static-boundary/run.py --source PATH_TO_SOURCE_CLONE --check
python experiments/records/public-p20-static-boundary/check.py --source PATH_TO_SOURCE_CLONE
```

The harness reads exact Git blobs, verifies SHA-256 hashes and revision, and executes the three scripts in a temporary directory. The [source's quick `verify.py`](https://github.com/emmanuel6474/liber-primus-p20-analysis/blob/a39e7de90ff9414791fe5f4f8d44540bd0bdb089/verify.py) has a separate defect: its hash manifest names `.gitignore` and `.github/workflows/verify.yml`, but neither file exists in that commit, so the quick check fails before reaching the mathematical assertions. This record runs the mathematical scripts directly; it does not report the quick verifier as passing. [The file-by-file intake](research/source-intake/emmanuel-p20-a39e7de.json) documents all 85 tracked files, 20 active analysis scripts and that limit.
