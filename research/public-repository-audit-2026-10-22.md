# Public repository intake, 22 October 2026

This is a worklist for source review, **not** a count of completed Liberpedia experiments or a census of every public Cicada idea.

The [candidate snapshot](public-repository-candidates.json) records three GitHub repository-name/description searches. They returned 94, 130 and 232 hits respectively; after deduplication, **327 repositories** are candidates. Search metadata alone says nothing about whether a repo contains original tests, copied files, runnable code, or valid conclusions. Repositories on other hosts, and even some known GitHub repos such as [Wulfic/Cicada3301-Liber_Primus](https://github.com/Wulfic/Cicada3301-Liber_Primus), did not match these queries. Do not describe the 327 as “all public repositories.”

## First source inspected

[Dukotah/cicada3301](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1), pinned at commit `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`. Its [machine-readable ledger](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/LEDGER.json) is 553,757 bytes (SHA-256 `7718bf90fb4cc6cc0fb98464d65ab898dd0e776da33d9b056bcd908d3b60558d`). It has **172 entries**: 49 labelled measured, 48 negative, 25 audit, 20 open, 15 partially run, 7 never run, 5 eliminated and 3 superseded. These are the repository's own statuses. In its negative category, 31 entries name a reproduction command and 44 name evidence files; their files, commands, controls, and findings have **not** been independently replayed here.

The ledger mixes research questions and units of work. Some statuses also refer to an English-specific scoring instrument and later restatements. An individual Liberpedia record should therefore pin the exact entry and files, recover the actual input and decoding rule, run its controls, and state only the bounded result. A ledger label alone must never be converted into “this method failed.” Existing Liberpedia records can be linked only after comparing their actual pages, symbols, parameters, and exclusions with the named entry.

Next source-review unit: screen the ledger's 48 negative entries for runnable, archived evidence; cluster equivalent sweeps before replay; start with entries whose inputs and positive controls are available. Record missing files explicitly. In parallel, inspect the other candidate repositories by stable revision and add their distinct methods to the same source-specific intake. No public-repository coverage percentage is warranted yet.

The first replay is [R23-A2 printed-line acrostics](dukotah-r23-a2-source-audit-2026-10-22.md). Its commands reproduce the reported 48-read result, but the planted controls do not pass the experiment's final family threshold. It remains a reported attempt, not an independently established negative.
