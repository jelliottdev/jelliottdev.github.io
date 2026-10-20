# How much freedom remains in a magic square?

## Question
Does a fixed line sum, half-turn symmetry and one fixed entry determine the rest of a five-by-five magic square?

No. Under precisely these conditions, five rational degrees of freedom remain. We also construct positive-integer alternatives to both LP1 examples, keeping any one chosen cell unchanged. This tests uniqueness of numerical grids, not a cipher or the authors’ intentions.

## Why this matters
It is tempting to count twelve line-sum equations, subtract twelve from the number of cells, and conclude that almost everything is forced. That subtraction only works for independent equations. For example, the sum of all row totals already equals the sum of all column totals. Symmetry creates further dependencies.

A **degree of freedom** is an independent parameter that can vary while all the equations remain satisfied. It is not a count of solutions and does not mean that every integer assigned to those parameters produces an allowed square.

## Scope and plan
The [recorded plan](experiments/records/magic-square-freedom/plan.json) specifies orders 3, 5 and 7, with four symmetry conditions each. Every row, column and both main diagonals have the same fixed sum. We distinguish:

- No additional symmetry.
- Half-turn symmetry: the cell at row r, column c equals its opposite after a 180-degree rotation.
- Transpose symmetry: swapping row and column leaves the entry unchanged.
- Both symmetries together.

The actual LP1-05 converted square and LP1-16 printed square have half-turn symmetry. Neither is transpose-symmetric: compare their cells at row 1, column 2 and row 2, column 1. Imposing transpose symmetry would therefore change the model and exclude both observed grids.

The supplied discussion had already proposed uniqueness, retracted that claim, and suggested possible dimensions. Those claims were known before calculation. This is a deterministic audit, not a blind prediction or significance test. The plan was written before running but was not externally timestamped or preregistered.

## Method
Let A be an existing square and D a change to it. The square A+D retains the same line sums exactly when every row, column and diagonal of D sums to zero. The same symmetry equations apply to D. Keeping one cell unchanged adds the equation that its change is zero.

The script forms these linear equations and reduces them with exact rational arithmetic. Rank counts the independent equations; dimension equals the number of cells minus rank. The saved nullspace basis describes all rational changes satisfying the equations. A uniform rational grid with entry equal to the line sum divided by the order supplies a solution for every prescribed rational sum, so the reported affine dimensions are not dimensions of an empty set.

For each of the 25 cell positions in each actual five-by-five square, the script selects the first basis vector that preserves that cell, clears denominators, and divides out the common integer factor. It tries adding that primitive change, then subtracting it. It stops after those two possibilities; this is not an exhaustive positive-integer enumeration.

## Results
All twelve comparison models completed. These dimensions assume a fixed common line sum:

| Order | No symmetry | Half-turn | Transpose | Both |
| --- | --- | --- | --- | --- |
| 3 | 2 | 0 | 1 | 0 |
| 5 | 14 | 6 | 8 | 4 |
| 7 | 34 | 16 | 19 | 10 |

For order five, fixing any one cell reduces the half-turn dimension from six to five. For order seven it reduces sixteen to fifteen. This is not a statement about an audited historical seven-by-seven square; order seven here is a mathematical comparison. For order three, the half-turn model already has dimension zero: with a fixed sum, it forces the uniform rational square.

Every one of the **50 fixed-cell tests** produced a different positive-integer square. Each preserves its original line sum and half-turn symmetry, and keeps the chosen entry unchanged. The complete [results and witnesses](experiments/records/magic-square-freedom/results.json) include all cases, bases, positions and input hashes.

### An example you can check by hand
Keep the center 809 in LP1-16. Add 1 to row 2, column 1 and row 4, column 5; subtract 1 from row 2, column 5 and row 4, column 1. Leave every other cell alone.

```text
 434 1311 312  278  966
 205  812 934  280 1070
 626  620 809  620  626
1070  280 934  812  205
 966  278 312 1311  434
```

Each affected row and column gains one and loses one. Neither diagonal changes. Opposite entries still agree, all entries remain positive, and every line still sums to 3301. Thus the center value 809 cannot uniquely determine the original grid under these rules. These numbers are a constructed counterexample, not a transcription correction.

## Reproduce
Python 3.12 standard library; no network, packages or AI calls. From the repository root, run:

```sh
python experiments/records/magic-square-freedom/run.py --check
python experiments/records/magic-square-freedom/check.py
```

The first command recomputes every case and compares the complete report. The second independently constructs the equations and checks rank modulo two large primes. It directly verifies every rational null vector and its independence. A matching modular rank gives a lower bound; the independent null vectors give the matching upper bound, certifying the rational rank. It also checks every positive-integer counterexample by summing its actual rows, columns and diagonals and comparing opposite cells.

Use `--write` instead of `--check` to regenerate results. Preserve the old output if changing the plan or input transcriptions.

## Retest and changes
On 20 October 2026, Codex recomputed the saved result and ran the separate checker. All twelve ranks, fixed-cell dimensions and fifty witnesses passed. This is computational review by the same agent; independent human review is pending. No model, bounds or criterion changed after inspecting the results.

## What remains open
This disproves uniqueness under the stated constraints. It does not count all positive-integer solutions, impose prime patterns or distinct entries, reconstruct a historical server validator, or show which values the authors deliberately selected. A rational basis is not automatically a basis for all integer solutions: clearing each vector’s denominators is enough to construct these witnesses, but is not an integer-lattice enumeration method.

An extra requirement can shrink the space. To test one, state it as a separate variant and show exactly which constraints changed. A theory that fixes many cells, restricts values to a list, or imposes a primality pattern is not ruled out by this result.

See [the magic-square guide](#/wiki/magic-squares) for the original images and rune-value conversion, and [search space and bounds](#/wiki/search-space) for why a claim must name the space it covers.
