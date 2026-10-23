# Three QuagMirror drafts beyond the six-rune example

The [six-rune draft](#/experiments/quagmirror-six-rune-replay) is one of four scripts in the same [pinned public repository](https://github.com/sgroveman/cicada3301_lp/tree/88ef1e60b0738b8b28db96bc9dc44dc4da8dd307/Solving%20Attempts). We ran the other three **as written**, including their fixed debug stops and handwritten mirror tables. All start from the same 729 source rune indices covering LP2-00–02. The indices match Liberpedia's page transcription after treating the two printed forms of the J rune as the same alphabet position.

## Finding

The scripts process **49, 153 and 500 positions** respectively. Each produces short English-like fragments mixed with unreadable text. None processes its whole 729-rune input, supplies a planted recovery control, or checks a reading on held-out text. Reproducing these outputs establishes what the drafts actually do; it does not establish a plaintext for LP2.

![The original script stops after 153 runes, version 4 after 49, and the WIP script after 500; page boundaries occur after 262 and 528.](experiments/records/quagmirror-variant-continuations/coverage.svg)

| Script | Positions | Beginning of its output |
| --- | ---: | --- |
| Original | 153 | `DIUINITY WITHIN HAUING BOTH IHING...` |
| Version 4 | 49 | `DIUINITY WITHIN PRAY FOR ANY CORRUPTIBLE...` |
| WIP | 500 | `DIUINITH WITHIN EUEN DIATH OSW...` |

These are **three different drafts**, not three confirmations of one decryption. Their rules and stopping points differ. Version 4 contains a pass-through at source index 17 that uses `continue` before the loop counter advances. Its nominal `index >= 48` debug stop therefore occurs after **49 input positions**. We retain that behavior; silently changing it would create another method. The [complete outputs and numeric streams](experiments/records/quagmirror-variant-continuations/results.json) are saved so a promising fragment can be read in context rather than selected in isolation.

## What the replay checks

Each script contains nine 29-symbol substitution tables, a hard-coded 729-index ciphertext, a numerical recurrence, and a Latin-fragment mapping. The [checker](experiments/records/quagmirror-variant-continuations/check.py) confirms that the tables are permutations, the source ciphertext matches the 729 runes on LP2-00–02, the printed numeric rows have the stated lengths, and the printed final text follows from those numeric outputs and the script's own spacing marks. This independently checks the **input and output trace**; it is not an independent proof that the recurrence recovers meaningful plaintext.

The first fragments may look deliberate. Assessing them requires the full output, a fixed method for every rune, a criterion chosen before seeing the result, and a positive control showing that the program can recover a known message made with its proposed cipher. The source drafts provide no such control. The longer WIP output is valuable evidence of how the apparent opening continues under the same code, but it does not by itself validate or refute every QuagMirror-style method.

## Reproduce

From a Liberpedia checkout with Python 3 and SymPy installed:

```bash
python experiments/records/quagmirror-variant-continuations/check.py
python experiments/records/quagmirror-variant-continuations/run.py
```

The runner executes the three bundled [pinned scripts](experiments/records/quagmirror-variant-continuations/source/OG_quag_mirror.py), extracts their complete printed output tables, and compares the results with the saved file. Their source revision is `88ef1e60b0738b8b28db96bc9dc44dc4da8dd307`; the record lists every file hash. No word choice, table, or stop point is adjusted during the replay.
