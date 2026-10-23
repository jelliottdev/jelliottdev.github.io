## Finding

The pinned source reports a sweep of **884,000 seed words** across four Python 2.7-style keystream configurations. It saved **95 candidates** that passed its first screen. We can check those saved rows: they divide into **21, 25, 24 and 25** by configuration, and none clears the source's final score bar of **7.6342**. Their highest final score is **6.248**. The underlying 884,000 first-stage scores were *not* saved, so the sweep total and the claim that no omitted candidate passed remain source-reported rather than independently recomputed here.

The source's planted-key control passes **4/4** in its saved output, but it begins at the **full 240-rune evaluation**. The actual sweep first applies a **120-rune, narrower-beam screen** and promotes a word only when that score reaches **5.0**. The control never calls this screening function. It therefore shows the final evaluator can recognize its own planted text; it does **not** measure whether the first gate would pass that text. The exact model file needed to try the gate is missing from the pinned public repository, as are three of the corpus files required to rebuild it.

![The actual sweep has a first screening gate that the planted control skips.](experiments/records/py27-reducer-sweep-source-audit/screen-control-gap.svg)

This is a **source-method audit**, not a new negative decryption result. The saved rows support a narrower statement: *among the 95 recorded promotions, no candidate met the published final score threshold.* They do not establish a measured false-negative rate for Stage A or a ruling on Python-derived keystreams in general.

## What was in the source sweep

| Rune reducer / seed map | Screened, reported | Saved promotions | Best saved final score |
|---|---:|---:|---:|
| `getrandbits(5) % 29`, one word | 288,000 | 21 | 6.089 |
| Reject `getrandbits(5)` values 29–31, one word | 216,000 | 25 | 5.260 |
| Repeated shuffle of 29 values, one word | 186,000 | 24 | 6.248 |
| `int(random() × 29)`, two-word seed map | 194,000 | 25 | 5.341 |

The source orders **433 proposed seed words**, expands neighborhoods around its top 64, and deduplicates them to **45,975** words before a dense count from zero. We independently reconstructed that ordering from the pinned seed-prior file. The recorded screen counts are each larger than 45,975, consistent with the source's statement that it completed this front in every configuration. Because only promoted rows were persisted, their actual first-stage scores and the rest of each scan cannot be audited from the receipts alone.

There is a small but concrete reporting error: the prose says **71 of 95** promotions had both recovery fields equal to 1.000. The pinned rows contain **67**. This does not change the observed zero final-bar clearances, but it illustrates why the rows matter more than summary prose.

## Scope and how to retest

The source decodes the **first 120 runes of LP2-00** for screening and the **first 240** for its final gate. Its key is a seed word passed through one of the four specified reducer/map combinations. The searched fractions of each nominal 2³²-word space are roughly **0.004–0.007%**. The two-word map is a deterministic 32-bit-to-64-bit fold used by the source, not an enumeration of all 64-bit Python hash values. Other seeds, other reducers, other cipher relations and plaintexts outside the source's scoring panel remain untested here.

The [pinned sweep code](experiments/records/py27-reducer-sweep-source-audit/source/liber-primus/analysis/round21/L3-py27-reducers-plus-64bit-map/sweep.py), [planted control](experiments/records/py27-reducer-sweep-source-audit/source/liber-primus/analysis/round21/L3-py27-reducers-plus-64bit-map/poscontrol.py), [saved rows](experiments/records/py27-reducer-sweep-source-audit/source/liber-primus/analysis/round21/L3-py27-reducers-plus-64bit-map/reducers_sweep.jsonl) and [aggregate](experiments/records/py27-reducer-sweep-source-audit/source/liber-primus/analysis/round21/L3-py27-reducers-plus-64bit-map/out_reducers.json) are included with hashes. Reconcile them without the absent model using:

```text
python experiments/records/py27-reducer-sweep-source-audit/run.py --check
python experiments/records/py27-reducer-sweep-source-audit/check.py
python experiments/records/py27-reducer-sweep-source-audit/plot.py --check
```

To establish the broader negative, first restore the original `panel.npz` or its exact training inputs, then run the **complete planted control through Stage A and Stage B**. Persist each screened word's first-stage score or a verifiable checkpoint before repeating the bounded sweep. The original [preregistration](experiments/records/py27-reducer-sweep-source-audit/source/liber-primus/analysis/round21/L3-py27-reducers-plus-64bit-map/PREREG.md) describes that intended bound; the [source manifest](experiments/records/py27-reducer-sweep-source-audit/source-manifest.json) identifies the bytes audited here.
