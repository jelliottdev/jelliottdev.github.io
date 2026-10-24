The fixed five-entry pattern for **Volans fits the five dots most closely**, with a typical mismatch of about 35 pixels, measured as root mean square (RMS). Orion, Aquila and Boötes fit less closely. This comparison does not identify a constellation or explain a cipher: other generated five-point shapes also achieve fits this close after the same complete search.

The primary measurement uses [LP2-07](#/reader/lp2-07). The [existing five-dot comparison](#/wiki/dots?section=five-dot-geometry) establishes that its pattern repeats on LP2-23 and LP2-56. Those appearances are checked here for robustness, not counted as independent observations.

## What the overlay shows

Filled markers show the existing measured dot centres. Open markers show fitted catalogue entries. Dashes connect each star entry to its assigned dot. Every panel uses the same pixel scale; marker sizes are symbolic. These are point plots, not manuscript images or traditional constellation line drawings.

The figure shows the best of the fixed 88 candidates and the three named leads. Every other candidate's minimum, rank, transform and residual vectors remain in [the complete results](matching-results.json). [The overlay points](visual-data.json) retain both original-image centroid coordinates and fitted star coordinates for inspection.

| Fixed five-entry candidate | Rank among 88 | Normalized RMS | RMS miss, pixels | Largest miss, pixels |
| --- | ---: | ---: | ---: | ---: |
| Volans | 1 | 0.114079 | 34.87 | 55.02 |
| Boötes | 24 | 0.312279 | 95.45 | 141.05 |
| Orion | 69 | 0.452143 | 138.21 | 232.55 |
| Aquila | 72 | 0.475296 | 145.28 | 216.74 |

“RMS miss” is the root mean square of the five Euclidean residual distances. The normalized value divides that distance by the dot pattern's RMS radius. Smaller values mean a closer shape fit. All numbers in this table use the preselected LP2-07 pattern.

## A fixed catalogue rule

Each constellation contributes its **five brightest eligible catalogue entries**, ranked by visual magnitude and then HR number in the Bright Star Catalogue, fifth edition. Membership follows the pinned Roman boundary lookup on fixed J2000 coordinates. This is one explicit star-selection rule; it does not represent every asterism, traditional line drawing, five-star subset or interpretation of a constellation name.

The named inputs are Orion HR1713/2061/1790/1903/1948; Aquila HR7557/7525/7235/7710/7377; and Boötes HR5340/5235/5506/5435/5681. The full library contains 88 candidates. Fourteen documented nonstellar catalogue rows are excluded; the remaining 9,096 entries all have usable coordinates and magnitude. Equal magnitudes use integer HR order. No proper-motion correction, epoch adjustment, hand replacement or photometric tuning was applied.

Distinct catalogue components remain distinct. Three selected pairs lie within 60 arcseconds: Centaurus HR5459/5460, Crux HR4730/4731 and Gemini HR2891/2890. Consequently, five catalogue entries are not always five unresolved naked-eye points. These cases were retained and flagged rather than removed after seeing their fits.

Each fixed five-entry set is projected onto one gnomonic plane centred on its unweighted mean unit direction. Every candidate receives all 120 point correspondences and both reflected and unreflected branches. Translation, rotation and one uniform scale are fitted; anisotropic stretching, shear, star omission and alternate projection centres are excluded. That makes 21,120 labelled registrations per query, all parts of one bounded measurement.

The dot inputs are the previously exported threshold-140 centroids, with their original image hashes and component rules. No new dots were measured, and no crop, threshold or centroid was chosen to improve a star fit.

## Two complete-search references

A candidate's apparent closeness must be considered alongside the many alignments searched. Both predefined reference generators therefore repeat the complete 88 × 120 × 2 selection for every generated query.

| Reference generator | Complete searches at least as close as LP2-07 | Plus-one fraction | Monte Carlo interval for that generator |
| --- | ---: | ---: | ---: |
| Five independent uniform-disk points | 171 / 4,095 | 172 / 4,096 ≈ 4.20% | 3.60–4.83% |
| Five catalogue entries sampled within a randomly selected constellation | 243 / 4,095 | 244 / 4,096 ≈ 5.96% | 5.25–6.70% |

The intervals are Wilson 95% intervals for simulation uncertainty in each specified generator's fraction. They do not quantify uncertainty about astronomical meaning or the artist's intent. These are exploratory conditional shape references, **not confirmatory probabilities of a constellation or decryption**. The generators are choices too: random disk points and random catalogue sets do not model every way artwork or a proposed sky pattern could arise. No reference draw required rejection; all 8,190 planned queries were retained.

For the three named leads, almost every reference search fits at least as closely: 4,093/4,095 under each generator for Boötes, and all 4,095 for Orion and Aquila. The saved results retain the same whole-search comparisons for every candidate, not just the selected best.

## Repeated artwork and controls

LP2-23 and LP2-56 also select Volans, at normalized RMS 0.114146 and 0.114155, with RMS misses of 34.89 and 34.90 pixels. Their agreement is expected for a repeated dot pattern. There is no best-of-three target choice or combined probability.

Before any target score, the frozen fitter was compared with an independent SVD implementation on 96 mathematical fixtures, including collinear, nearly collinear, repeated-point and symmetric cases. All 88 transformed exact catalogue plants retain their true candidate in the optimum tie set. All 1,408 noisy plants also rank their true candidate first or tied at the two specified noise levels. [The complete gate receipt](pretarget-gate.json) preserves every outcome; none was omitted. These controls establish recognition of the fixed library under these perturbations, not the correctness of the astronomical hypothesis.

The target and reference runner was then hashed and authorized against the unchanged [frozen plan](matching-plan-frozen.json). Independent SVD checks reproduce all 63,360 target registration scores and all 264 candidate witnesses, with maximum normalized score disagreement below 3.4 × 10⁻¹⁶. All 528 saved reference counts are independently recounted; 16 predeclared reference samples also undergo complete-search SVD checks. The target fits took 0.029 seconds; the two reference campaigns took 13.74 seconds each, with total execution time 27.72 seconds on the task runtime.

## Reproduce and inspect

The experiment bundle contains the frozen catalogue, membership, projections, centroid export, input hashes, code and saved results. Matching is offline and requires NumPy 2.5.4. The original candidate-preparation environment is documented separately with Astropy 8.0.2 and its pinned dependencies; matching does not redownload a catalogue or redo membership through a different version.

```text
python experiments/records/dot-constellation-candidate-fit/run.py --check
python experiments/records/dot-constellation-candidate-fit/check.py
python experiments/records/dot-constellation-candidate-fit/replay_gate.py
python experiments/records/dot-constellation-candidate-fit/plot.py --check
```

The first command repeats all three targets and both 4,095-query references without writing expected outputs. The independent checker uses SVD rather than the optimized fit. The gate replay compares every mathematical and plant outcome while ignoring timing differences, again without overwriting the original pre-target receipt. All candidate minima and reference-query coordinates are available for inspection, including a numerical tie policy of 10⁻¹².

Catalogue attribution: Hoffleit and Warren (1991), *The Bright Star Catalogue*, fifth revised preliminary edition, CDS V/50; [CDS/VizieR catalogue and documentation](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/V/50?format=html). The preserved VizieR usage notice permits scientific use with original-author/publication attribution; it is not an MIT licence. Roman membership lookup is from the pinned [Astropy constellation implementation](https://docs.astropy.org/en/stable/api/astropy.coordinates.get_constellation.html), with its BSD terms retained in the bundle.

The separate [shared-radii experiment](#/experiments/compass-shared-radii) tests a compass construction on different dots. Its result does not supply a star-identification rule here. Rune selection, reading instructions, astronomical intent and plaintext recovery remain outside this measurement.
