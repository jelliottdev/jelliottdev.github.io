# Synthetic matching gate: ready for review

**Stopped before real artwork or reference-query scoring.** No LP2 centroid coordinates were loaded by the preflight; the frozen artwork file was only hash-checked. Neither of the two whole-search reference seeds has been used. Work remains entirely within this intake and the isolated runtime.

The approved rule remains one exploratory measurement: five brightest catalogue entries in each of 88 constellations, fixed J2000 projection, all 120 correspondences and both orientation branches. Close catalogue components remain flagged and retained. There is one primary artwork query, LP2-07; the other appearances remain repeat-artwork robustness checks, not independent observations.

## Frozen implementation and inputs

`matching-plan-frozen.json` SHA-256:

`26ca51b70daf04ac798663053a517bc02d6d7cdd162279ed8e45dd1f6b4391a7`

All sixteen declared input/code hashes passed before and after the gate. `similarity.py` computes every labelled registration using exact 2D orthogonal-similarity arithmetic. It evaluates residual vectors directly, avoiding subtraction of nearly equal energies near a perfect fit. `svd_reference.py` independently fits the original unnormalized points using SVD and shares no fitting code with the optimized implementation. Neither implementation omits permutations, orientation branches or constellations.

## Results

- **96 synthetic mathematical fixtures:** 69,120 registration scores checked against SVD, including collinear, nearly collinear, repeated-point and symmetric cases.
- **88 exact transformed plants:** every source constellation is in the optimum tie set and passes the frozen residual gate. All 1,858,560 full-library registration scores were also compared with SVD.
- **1,408 noisy plants:** all 704 at noise σ = 0.001 of shape RMS radius and all 704 at σ = 0.01 rank their source constellation first or tied. There are no omitted failures. These controls test recognition of this fixed candidate library, not unique recovery of star labels or astronomical meaning.
- **Largest optimized-versus-SVD score difference:** (4.4409\times10^{-16}), below the frozen (10^{-12}) tolerance.
- **176 complete-search timing trials:** mean 3.12 ms, maximum 4.18 ms per 21,120-registration query. At the measured mean, the two planned 4,095-query reference campaigns project to about 25.52 seconds combined, excluding query generation. This is a synthetic projection, not a measured reference or target runtime.

`pretarget-gate.json` retains every mathematical fixture summary, exact-plant witness, noisy outcome and rank. All results are implementation and sensitivity checks. They are not evidence for a constellation in LP2 or confirmatory probabilities.

The next authorized stage would require review of this gate before scoring the primary pattern or either predefined reference campaign. No public record, shared data, build or commit has been created by this stage.
