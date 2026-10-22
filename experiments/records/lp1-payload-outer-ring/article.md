# What remains when the four LP1 message borders are removed?

The four signed messages hidden in **LP1-10–13** display the same seven-row ASCII number diagram with a changing outer digit. In page order, the border digits are **3, 3, 0, 1**. Remove the top and bottom rows and the first and last character from each remaining row: the interior is byte-identical in all four messages, without rotation or reflection.

![Four ASCII diagrams with their changing perimeter marked in orange and common interior in blue](experiments/records/lp1-payload-outer-ring/four-borders-one-interior.svg)

This checks a reported observation connected to the solved text's phrase about *shedding the circumference*. The source note says removing the outer number of each repeated square leaves an identical number grid. It does **not** supply an LP2 decryption rule or an output. The match is a property of the four embedded messages, not evidence that stripping a perimeter solves an unsolved manuscript page.

## The four source objects

Each page image has an extracted OutGuess payload containing a PGP-signed instruction. The repository retains the exact body text and page metadata recording successful signature verification. This audit rechecks the body hashes and that recorded verification status; it does not independently re-run GPG. The bodies instruct the reader to create a Tor hidden service and submit three magic squares. Their diagrams have the same spacing and numeric interior. LP1-10 and LP1-11's whole body files are byte-identical; LP1-12 and LP1-13 change the diagram's border digit.

| Embedded body | Border digit | Retained numeric rows |
| --- | ---: | --- |
| LP1-10 | 3 | `10 12 10` / `12 14 12` / `10 12 10` |
| LP1-11 | 3 | Same |
| LP1-12 | 0 | Same |
| LP1-13 | 1 | Same |

The [fixed plan](experiments/records/lp1-payload-outer-ring/plan.json) defines the operation before comparison. It requires exactly one diagram bounded by two 16-character rows of equal digits; removes only that one-character perimeter; retains spacing in the five interior rows; and parses the three numbered rows. The [complete result](experiments/records/lp1-payload-outer-ring/results.json) preserves every original and retained line, the source hashes, and the derived matrix.

The common matrix is:

```text
10  12  10
12  14  12
10  12  10
```

Its row sums are **32, 38, 32**. It is therefore not a magic square under the ordinary equal-row-sum definition. The border sequence happens to read `3301` in page order; the audit does not infer a further instruction from that fact.

## A distinct reading that fails

There are also two *visible* five-by-five LP1 squares: the mixed number-and-rune square on LP1-05, which needs Gematria Primus conversion, and the decimal square on LP1-16. If “remove the outer ring” is instead applied to those, their central three-by-three grids differ:

```text
LP1-05 converted       LP1-16 printed
199 130 320            812 934 280
245  91 245            620 809 620
320 130 199            280 934 812
```

None of the five-by-five core values occurs in the other core. Rotation or reflection cannot make them identical. These are not the repeated signed-message diagrams described in the source discussion. Keeping the objects separate matters: the same verbal instruction cannot be reported as verified on a different pair of squares.

## Reproduce the comparison

From the repository root, with Python 3 and no added packages:

```text
python experiments/records/lp1-payload-outer-ring/run.py --check
python experiments/records/lp1-payload-outer-ring/check.py
python experiments/records/lp1-payload-outer-ring/plot.py --check
```

The run script extracts the diagrams from four hashed message bodies and converts the separate LP1-05 and LP1-16 page transcriptions for the exclusion check. The independent checker parses the ASCII blocks with a different pattern and compares all four exact lines and all nine core values against an explicit oracle. The result is an input and source-identity audit. It does not test whether a perimeter-removal operation helps decrypt LP2.
