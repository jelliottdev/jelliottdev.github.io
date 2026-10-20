## The model being tested

On each of [LP2-33](#/reader/lp2-33) and [LP2-39](#/reader/lp2-39), label the three horizontal dots A, B and C from left to right. Draw three circles centered at those dots. Can the circles meet at one point on each page if **the same ordered radii** are used on both pages?

The two target points may differ. The radius at A must be the same on both pages, likewise B and C. Both pages remain at their original 2400 × 3600 pixel scale; no resizing or refitting is allowed. This is one precise compass construction, not a general test of compass-related ideas.

**Result: no**, for the measured dot centers at each of the three declared grayscale thresholds. An exact rational distance bound rules out every possible ordered radius triple within this model. It does not require selecting radii from the number square or searching a finite list.

## Measure the centers first

The script reads the original JPEGs, converts RGB to Pillow’s L grayscale, and finds four-connected dark components inside two declared crop boxes. Pixel coordinates are zero-based, with integer coordinates at pixel centers. Crop right and bottom edges are exclusive.

| Page | Crop (left, top, right, bottom) |
| --- | --- |
| LP2-33 | (576, 1656, 1824, 1836) |
| LP2-39 | (1200, 1638, 1800, 1746) |

For each threshold 100, 140 and 180, a pixel is dark if its grayscale value is strictly below the threshold. Retain components with area greater than 200 pixels, width/height strictly between 0.7 and 1.3, and filled area greater than 60% of the bounding rectangle. Exactly three components must survive; otherwise the script stops.

Each center is the arithmetic mean of its component’s pixel coordinates. The report stores integer coordinate sums and areas, so the subsequent calculation uses exact fractions rather than rounded coordinates. This measures a particular thresholded shape; it is not an assertion that the author placed the dot at that exact rational point.

At threshold 140, the adjacent center separations on LP2-33 are approximately 417.47 and 478.23 pixels. On LP2-39 they are 196 and 224.5 pixels. The diagram uses one horizontal scale for both pages and separates the rows vertically for readability. It does not show the original vertical positions.

## Why three distances impose a constraint

Let Q be the perpendicular projection of B onto the line through A and C. Write `Q=(1−t)A+tC` and `e=B−Q`. The dots are almost collinear; e measures the middle dot’s small displacement from that line. Let `K=t(1−t)|C−A|²`.

If X is a target point with distances rA, rB and rC from the three dots, expanding the squared distances gives:

```text
rB² − (1−t)rA² − t rC² + K
  = 2 e·(Q−X) + |e|²
```

The right-hand side is an affine function of X. Its minimum and maximum over a rectangle occur at corners, so evaluating the four page corners gives an exact residual interval. No grid sampling of target points is necessary.

Now compare the two pages. Their shared radii cancel except for `(t₂−t₁)(rA²−rC²)`. Each squared radius lies between zero and the squared page diagonal, because both its center and target lie on the page. Consequently:

```text
|residual₂ − residual₁|
  ≥ |K₂ − K₁| − |t₂ − t₁| × (2399² + 3599²)
```

The two corner intervals also give an upper bound on that absolute difference. If the lower bound exceeds the upper bound, no target pair with shared radii can exist.

## The bounds

The table rounds displayed values to two decimal places. Decisions use exact fractions saved in the report; the unit is squared pixels.

| Threshold | Required lower bound | Allowed upper bound | Compatible? |
| --- | --- | --- | --- |
| 100 | 153,322.33 | 119.47 | No |
| 140 | 155,146.71 | 14.17 | No |
| 180 | 153,854.17 | 11.88 | No |

All three declared threshold variants give the same exclusion. This is a sensitivity check, not a confidence interval or a complete treatment of measurement error. The argument treats each measured center as fixed; it does not quantify every plausible alternative center, crop or dot-selection rule.

## Reproduce

Extract the experiment bundle, then extract the [original-images ZIP](downloads/original-images.zip) into the same folder so that `images/lp2-33.jpg` and `images/lp2-39.jpg` are available. Original images are separate from the small experiment ZIP. Install Pillow 11.3.0 in your Python environment, then verify the required image hashes and run:

```text
python scripts/verify_bundle.py EXPERIMENT-compass-shared-radii-IMAGE-INPUTS.json
python experiments/records/compass-shared-radii/run.py --check
python experiments/records/compass-shared-radii/check.py
```

The producer uses Pillow 11.3.0 and Python’s standard library. Its version is recorded so a different image-decoding environment does not silently claim an exact replay. The checker needs only the standard library. Neither command calls AI or accesses the network.

The producer reruns component measurement and the rational certificate. The separate checker verifies source hashes and reconstructs the projection parameter from squared side lengths. It obtains residuals by directly expanding distances to the page corners, without importing the producer. It verifies that identical page geometry is not rejected by the bound. It does **not** independently segment the images or provide a manual review of the dots.

Both checks passed on 20 October 2026. The procedure and controls were recorded in `plan.txt`; the declared thresholds, crops and target rectangle were unchanged after the run. This freshly reconstructs a constrained claim in the supplied research archive; it is not a new discovery. Human review remains pending.

## What remains outside this result

Rescaling one page, using different radii on each page, changing which dots receive which radii, placing a target outside the page, stepping a compass between points, or reading pairwise intersections changes the model. Those alternatives are not excluded here. The result supplies no rune selection or plaintext claim.

For the distinction between an illustration and a specified cipher, see [compass constructions](#/wiki/compass-cipher-tests). For coordinate conventions and original files, see [image regions](#/wiki/image-regions). For how to state this exclusion without overstating it, see [search space and bounds](#/wiki/search-space).
