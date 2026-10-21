# Guarded OutGuess diagnostic pilot

This is research preparation, not a published Have we tried it record. The plan and runner were committed as `4210429` before the fresh 20 October 2026 run. The existing guarded binary's hash matches its archived build record; both patched source files match their recorded hashes and exact edits after CRLF normalization. This is not a clean rebuild establishing binary-to-source correspondence.

## Fixed scope and result

Ten positive controls ran first, with the runner set to stop on a control failure. All ten matched their expected payload hashes. The same key, original JPEGs and 20-second timeout as the baseline were retained. Three further images were selected from known baseline outcomes, not randomly or as held-out cases.

| Image | Baseline | Guarded pilot | Byte comparison |
| --- | --- | --- | --- |
| LP1-06 | Exit 0, unverified output | Exit 0, unverified output | Same 58,152 bytes |
| LP1-05 | Exit 1, length rejection | Exit 1, length rejection | Same empty output |
| LP1-14 | Exit 3221225620 | Exit 1, explicit iterator guard | Same empty output |

LP1-14 reports `Guard: iterator skipmod zero at off=645437 bits=645682`. The explicit zero check precedes the remainder operation in the recorded iterator patch. This narrows the diagnostic for this guarded run; it is not a baseline crash stack trace, a finding about all 41 abnormal cases, or evidence that the image has no hidden data. LP1-06 remains unverified bytes despite an unchanged successful exit.

## Reproduce and audit

Run `python experiments/records/outguess-guard-pilot/check.py` from the repository to audit saved inputs, payloads and the comparison without executing OutGuess. To repeat retrieval with the exact declared binary, use:

```text
python experiments/records/outguess-guard-pilot/run.py --outguess /path/to/outguess --check
```

The runner requires the planned binary hash. A different binary is a different comparison. It does not fetch or install executable software.

## Before publication

Document a distributable, reproducible build procedure and independently check the full claim. Keep this pilot separate from any later 77-image sweep, and retain its preselected scope. No general success, payload-validity or hidden-data absence claim follows from these 13 cases. Human review remains pending.
