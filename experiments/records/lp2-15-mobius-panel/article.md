# Möbius values of the LP2-15 number panel

A [reported suggestion](#/wiki/reported-attempts?section=lp2-15-mobius-square-transform) applies the arithmetic Möbius function to the numbers at the top of [LP2-15](#/reader/lp2-15). This is a small but exact question: what comes out when we transform **all sixteen printed entries in place**? The source transcript refers to an output image that is not retained in the supplied text, so this is a reconstruction of the stated operation, **not an exact comparison with that historical image**.

The numbers in the upper part of each cell below are printed on the page; the `μ` values beneath them are calculated. The red `3299` stays in its original row and column. Neither a Fibonacci spiral nor subtraction from 3301 is applied here.

![Four-by-four LP2-15 panel showing each printed decimal number above its calculated arithmetic Möbius value. Only the second row is nonzero.](experiments/records/lp2-15-mobius-panel/panel.svg)

[Open the diagram](experiments/records/lp2-15-mobius-panel/panel.svg) · [View the original page](images/lp2-15.jpg)

The output matrix, in printed row order, is:

| Row | Column 1 | Column 2 | Column 3 | Column 4 |
| --- | ---: | ---: | ---: | ---: |
| 1 | 0 | 0 | 0 | 0 |
| 2 | −1 | −1 | −1 | +1 |
| 3 | 0 | 0 | 0 | 0 |
| 4 | 0 | 0 | 0 | 0 |

For a positive integer `n`, the arithmetic Möbius function is **zero if a prime square divides `n`**. Otherwise it is `−1` for an odd number of distinct prime factors and `+1` for an even number. That rule accounts for each cell; no visual judgement is required to obtain this matrix.

| Printed cell | Factorization | μ |
| --- | --- | ---: |
| r1c1 · 3258 | 2 × 3² × 181 | 0 |
| r1c2 · 3222 | 2 × 3² × 179 | 0 |
| r1c3 · 3152 | 2⁴ × 197 | 0 |
| r1c4 · 3038 | 2 × 7² × 31 | 0 |
| r2c1 · 3278 | 2 × 11 × 149 | −1 |
| r2c2 · **3299, printed red** | 3299 (prime) | −1 |
| r2c3 · 3298 | 2 × 17 × 97 | −1 |
| r2c4 · 2838 | 2 × 3 × 11 × 43 | +1 |
| r3c1 · 3288 | 2³ × 3 × 137 | 0 |
| r3c2 · 3294 | 2 × 3³ × 61 | 0 |
| r3c3 · 3296 | 2⁵ × 103 | 0 |
| r3c4 · 2472 | 2³ × 3 × 103 | 0 |
| r4c1 · 4516 | 2² × 1129 | 0 |
| r4c2 · 1206 | 2 × 3² × 67 | 0 |
| r4c3 · 708 | 2² × 3 × 59 | 0 |
| r4c4 · 1820 | 2² × 5 × 7 × 13 | 0 |

Twelve entries vanish; the only nonzero row is `−1, −1, −1, +1`. All but the red entry are even, but **evenness alone does not imply μ = 0**: the three other numbers in row 2 are squarefree. The table shows which prime square makes every zero. The row alignment is an observation of this fixed transform, not a decryption or a significance estimate after possible functions and arrangements have been considered.

## Reproduce it

From a checkout or the experiment download, run:

```text
python experiments/records/lp2-15-mobius-panel/run.py --check
python experiments/records/lp2-15-mobius-panel/check.py
python experiments/records/lp2-15-mobius-panel/plot.py --check
```

The [plan](experiments/records/lp2-15-mobius-panel/plan.json) fixes the source page hash and all sixteen inputs. The producer uses integer factorization; the separate checker searches independently for prime-square divisors and counts distinct prime factors. The [results](experiments/records/lp2-15-mobius-panel/results.json) preserve every coordinate, number, factorization, calculated μ value and the matrix. The diagram is generated from that ledger. The source transcript is identified by hash in the [reported-attempt register](#/wiki/reported-attempts?section=lp2-15-mobius-square-transform), rather than reproduced without its missing image.

**What this establishes:** the stated arithmetic operation is reproducible on the complete printed panel. It does not show that this was exactly the unseen image in the discussion, that a particular row or spiral is a key, or how a `−1/0/+1` stream would act on the runes. A solving test would first have to fix that operation, its order, boundaries and acceptance criterion, then compare continuous output with controls.
