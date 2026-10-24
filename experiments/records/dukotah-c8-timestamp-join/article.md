# Do the archived texts supply a date for each target page?

The C8 proposal chooses public random data by the creation time in each page's PGP signature. A replay of its Step 0 extracts eight signature blocks with seven distinct seconds. An independent packet parser and section-boundary check places every block in LP1. The preserved LP2 portion contains no signature armor; its 24 headings group page labels through 57. The separate runic transcription contains 57 percent-delimited segments and no signature armor. These units are distinct.

This establishes that these two textual inputs do not supply the proposed per-target-page join. It does not establish that every historical image or distribution lacked signatures, or exclude a dated-pad cipher using another explicit join rule. The replay performs no signature verification. G-02 separately checks preserved signed-file bytes against a specified key; signature validity and section attribution are different checks. Signature creation times remain signer-supplied clock values, not independently authenticated release dates.

The pinned C8 source also reports a 630-test decoder probe and positive controls. Those results were not rerun here: the pinned cache contains timestamps.json but no beacon XML, and the decoder imports the separately gated I2 stack. They are not evidence for this record's outcome.

Run `python experiments/records/dukotah-c8-timestamp-join/run.py` to replay the source extraction unchanged in a temporary local tree, compare it with the saved result, and run the independent parser. No network access is used.
