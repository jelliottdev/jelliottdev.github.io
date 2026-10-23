# Six keyed OutGuess probes on LP2

## Result

Six fixed passphrases were tried against each of the 58 original LP2 JPEGs. OutGuess returned nonempty bytes in **232 of 348** runs. None of those byte streams passed the basic checks for a readable message or a common file header. The result is **inconclusive** about hidden data: a successful OutGuess exit does not authenticate its output.

![Count of nonempty retrievals for each of six keys. Bars count outputs, not messages.](experiments/records/outguess-keyed-lp2/figure.svg)

| Literal key | Nonempty outputs | Bytes per nonempty output |
| --- | ---: | ---: |
| `3301` | 24 / 58 | 54,051 |
| `LIBER PRIMUS` | 57 / 58 | 29,932 |
| `GEMATRIA PRIMUS` | 47 / 58 | 47,513 |
| `CIRCUMFERENCE` | 58 / 58 | 19,957 |
| `DIVINITY` | 34 / 58 | 51,011 |
| `SELF-RELIANCE` | 12 / 58 | 61,831 |

Each key produced exactly one nonempty output length across the pages, though the output hashes differ. Printable ASCII accounts for only 37.5–39.2% of those bytes. No output begins with a PGP, ZIP, PDF, PNG, GIF or JPEG header. These are descriptive checks, not a complete file-format classifier or a proof that no payload exists.

## What was tested

The six literal, case-sensitive phrases above were fixed before the 348-case run. They are a small manuscript-derived probe, not an exhaustive dictionary. The archive's historical keyed attempts were reviewed *after* this list had been frozen and did not change it. Original image bytes and the guarded OutGuess executable are fixed by SHA-256 in the [plan](experiments/records/outguess-keyed-lp2/plan.json).

The control first embeds a known 43-byte text into a separate synthetic JPEG under each key. Its six retained carriers recover that exact text only with their matching key: all **36 correct-key and cross-key checks** passed. Initial synthetic covers exposed a guarded retrieval-bound failure under one of the correct keys. The final 800×800 cover and six working carrier bytes were pinned before the LP2 grid; the exception and replacement are recorded in the plan. This control verifies that this build can recover a message when one is embedded under these keys. It does not validate the unsolved-page outputs.

This is a keyed extension of the [default-key OutGuess baseline](#/experiments/outguess-default-key). It checks this build, these six passphrases and these original JPEGs. Other passwords, transformed images, other steganography tools, and a modified OutGuess implementation remain outside its scope.

## Inspect or repeat

Download the experiment bundle and original JPEG archive, preserving their paths. [The saved receipt](experiments/records/outguess-keyed-lp2/results.json) lists every exit status, diagnostic, output size and SHA-256. [The output archive](experiments/records/outguess-keyed-lp2/outputs.zip) contains the exact 348 retrieved byte files, including empty ones, for independent inspection. A large binary output is not itself evidence of a message.

The bundle includes the [exact guarded Windows executable](experiments/records/outguess-keyed-lp2/tool/outguess-guarded-win64.exe) used for this run (SHA-256 `bdc1810e59cb1152e7c3da88b38eaedfe49eba1656b4a4ab6f8c2b3f40126273`) and its [copyright and license notices](experiments/records/outguess-keyed-lp2/tool/NOTICES.txt). This product includes software developed by Niels Provos. This software is based in part on the work of the Independent JPEG Group. Extract `outputs.zip` into a folder and, on Windows, run:

```text
python experiments/records/outguess-keyed-lp2/check.py --outguess experiments/records/outguess-keyed-lp2/tool/outguess-guarded-win64.exe --output-dir PATH/TO/outputs
```

This independently checks the original image hashes, all 348 retained output hashes and all 36 planted-key retrievals. To repeat the actual image grid, use `run.py --outguess experiments/records/outguess-keyed-lp2/tool/outguess-guarded-win64.exe --output-dir PATH/TO/new-output --check`. The run compares every receipt with the saved report and prints its counts; it does not replace the saved report. The executable's SHA-256 must match the plan; the [pinned upstream source](https://github.com/resurrecting-open-source-projects/outguess/tree/24810e14327c2bbeedeaadd3e24491f2a4425c02) and [guarded-build specification](experiments/records/outguess-guard-pilot/build-spec.json) document its source and patches. A rebuild under a different toolchain need not yield the same executable hash; compare it as a separate build.
