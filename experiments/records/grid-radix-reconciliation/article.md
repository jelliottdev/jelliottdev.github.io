# Does the grid use base 59 or base 60?

**Both are valid ways to number the 256 printed pairs, but they require different digit alphabets.** The archived grid transcription uses 59 of the 62 possible case-sensitive letters and digits: `f`, `y` and `z` do not occur. That count does not tell us the radix. A text can use fewer symbols than its alphabet permits.

The reported base-59 script explicitly deletes lowercase `f` from the candidate `0–9 A–Z a–x` alphabet and moves every later lowercase letter down one digit. Under that rule, `x` becomes 58, so base 59 is mathematically valid. Under the ordinary order without that deletion, `x` is digit 59 and **cannot** appear in a base-59 numeral. This is the difference between a custom alphabet and just changing 60 to 59 in a formula.

![Two digit alphabets: deleting an unused f moves g from 42 to 41 and x from 59 to 58.](experiments/records/grid-radix-reconciliation/digit-map.svg)

| Interpretation | `x` digit | `4F` value | Largest of 256 values | Fit in a byte? |
| --- | ---: | ---: | ---: | --- |
| Base 59, remove `f` and renumber | 58 | 251 | 251 | Yes |
| Base 59, keep ordinary digit numbers | 59 | — | — | Invalid: `x` is out of range |
| Base 60, ordinary digit order | 59 | 255 | 255 | Yes |
| Base 62, ordinary digit order | 59 | 263 | 263 | No: 12 entries exceed 255 |

The **byte condition matters**. If each pair must be exactly one unsigned byte and the ordinary digit order is fixed, the presence of `x` requires a base of at least 60, while `4F` must be at most 255 and therefore requires a base of at most 60. That makes 60 the only base *under those two assumptions*. Deleting `f` changes the digit assignments, so the base-59 proposal falls outside that conditional proof. Dropping the byte condition permits base 62 as a positional representation, though not as one byte per pair.

The two valid byte conversions are materially different: **220 of 256 values change** between custom base 59 and ordinary base 60 on the wiki text. For example, the first pair `3N` is 200 in the custom base-59 scheme and 203 in base 60. The fact that both produce 256 bytes does not identify which, if either, was intended.

## Which transcription was tested?

The pasted discussion includes a full 256-pair list. Its count of **59 observed characters** and **161 distinct pairs** reproduces, but that list differs from the wiki export at five coordinates: LP2-49 (6,6) `1L`/`1l` and (7,3) `0L`/`0l`; LP2-50 (11,6) `0l`/`0I` and (12,5) `2s`/`2S`; LP2-51 (8,7) `3i`/`3I`. These are the already documented [source transcription disagreements](#/wiki/seventh-onion-transcriptions?section=grid), not evidence for one base over another. They change the exact byte streams and their hashes under **both** encodings.

The more detailed transforms described later in the discussion are separate proposals. This audit does not replay those scripts, test routes through the grid or infer a plaintext. It fixes the elementary input and alphabet question so those experiments can state what they actually used. The [grid guide](#/wiki/alphanumeric-grids) explains the page layout and the conditional byte interpretation.

## Reproduce

Run `python experiments/records/grid-radix-reconciliation/run.py --check` from the repository or extracted experiment bundle. The [script](experiments/records/grid-radix-reconciliation/run.py) reads the coordinate-bearing [wiki grid export](exports/alphanumeric-grids.csv) and the [256 quoted tokens](experiments/records/grid-radix-reconciliation/source-tokens.txt), applies each declared alphabet and checks the saved [result table](experiments/records/grid-radix-reconciliation/results.json). It uses only the Python standard library. The quoted tokens came from the supplied September 2026 discussion; the original linked script files were not supplied, so this checks the displayed list and code excerpt, not an executable historical repository.
