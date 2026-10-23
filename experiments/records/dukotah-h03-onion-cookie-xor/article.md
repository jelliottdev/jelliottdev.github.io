# Do the onion cookies reveal text by XOR?

The [H‑03 source test](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round16/zeroFP) takes two 32-byte values from the 2013 onion cookies and XORs each with eight successive 32-byte blocks of four objects: the LP2-49–51 grid payload and three later onion RSA-hex blobs. We replayed its executable with the exact preserved inputs and independently recomputed every output byte.

![For each cookie and object, the most printable of eight XOR blocks remains below the 26-of-32-byte gate.](experiments/records/dukotah-h03-onion-cookie-xor/xor-maxima.svg)

**None of the 64 executed blocks reaches the source's 80% printable-ASCII gate.** The highest has **20 of 32** printable bytes, from cookie 761 with the fourth object. A deliberately planted 32-byte ASCII block is recovered by the original source function, so this threshold can detect that kind of output. The [complete 64-case table](experiments/records/dukotah-h03-onion-cookie-xor/cases.json) preserves the XOR bytes and counts.

## What the null covers

The source's written plan describes **128 trials** using both raw and hex-decoded cookie forms, plus digest and PKCS-structure checks. Its saved executable performs **64 trials using the hex-decoded form**. It applies the printable gate and records only a two-byte `00 01` hint; it does not execute the full written digest or padding tests. Our replay matches the executable and saved result, so the negative applies to **these 64 block-aligned XOR operations**, not to every use of the cookies as keys or the full written plan.

The remaining raw-form cases cannot be reproduced as written: each file contains **64 ASCII hex characters**, while the plan pairs a “32-byte cookie” with each **32-byte block** and never says which 32 raw characters to use or whether to repeat, truncate or change block size. We did not invent that rule. The plan also leaves the set and encoding of “known 3301 hashes/strings” unspecified.

A [separately frozen, retrospective diagnostic](experiments/records/dukotah-h03-onion-cookie-xor/structure-plan.json) checks the same 64 outputs for the source code's PKCS helper pattern, a stricter eight-`FF` padding pattern, and the one **20-byte AN END prefix** explicitly named in that code. All three yield **zero matches**; synthetic examples pass each predicate. This only addresses those exact structures in the executed 64 outputs. The helper accepts one `FF`, so its rule is not a general statement that a block is valid PKCS#1 padding.

The objects are exact local source bytes, including `canon_256.bin`; a different grid transcription would be a different input. No readable plaintext or new key is recovered here.

## Reproduce

The [replay plan](experiments/records/dukotah-h03-onion-cookie-xor/replay-plan.json) hashes the pinned source programs and six input files. Run from the repository root with Python:

```text
python experiments/records/dukotah-h03-onion-cookie-xor/run.py
python experiments/records/dukotah-h03-onion-cookie-xor/check.py
python experiments/records/dukotah-h03-onion-cookie-xor/structure.py
python experiments/records/dukotah-h03-onion-cookie-xor/plot.py
```

The first command runs the original H‑03 function and a temporary planted case. The second recomputes all 64 XORs without importing that function and compares the source's saved summary. This plan was frozen before our replay, **after** the source's result was available; it is not a new preregistration.
