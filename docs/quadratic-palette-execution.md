# Quadratic palette replication: execution notes

The scope and proof obligations are fixed in `experiments/plans/literal-prime-quadratic.md`. These scripts are preparation for a related variant of the literal-prime affine experiment. They do not yet constitute a published, reviewed experiment record.

From the repository root, with Python's standard library:

```sh
python -m unittest discover -s scripts -p test_quadratic_palette.py
python scripts/run_quadratic_palette.py --output quadratic-certificate.json
python scripts/check_quadratic_palette.py quadratic-certificate.json --receipt quadratic-audit.json
```

Choose new output paths for a rerun; both commands refuse to overwrite evidence. The certificate contains all 21,924 ordered, distinct anchor triples, either as a finite-divisor branch or an exact-image branch. It also retains any survivors, rather than assuming the historical result.

The checker does not import the producer. It constructs divisors from prime factors instead of paired square-root scanning, evaluates the interpolation expression in factored form, and solves the coefficient congruence through integer lifts rather than modular inverses. For the identity-anchor branch it directly scans all coefficient residues at every modulus from 110 through 321. Small-domain controls compare both solvers against every coefficient triple for moduli 2 through 18, including moduli divisible by 2 or 3.

The first producer run found 261,346 coprime-to-6 candidate moduli and 2,420,451 singular candidate moduli. These yield 261,346 and 7,993,284 coefficient checks respectively. It retained only the exact anchor branch `(2, 3, 5)` and found no nonidentity survivors. These are **producer results awaiting the complete independent audit**, not a claim of completed verification.

Before publication, retain the audit receipt, explain why the finite certificate covers every modulus above 109, add the branch diagram and scope counterexamples, and package a reproducible experiment alongside the existing affine family. In particular, distinguish a polynomial's coefficients from its function: nonzero quadratic coefficients can still represent the identity. Human review remains pending even after the computational audit succeeds.
