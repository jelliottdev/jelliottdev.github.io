# Browser families and evidence coverage

## Current vertical slice

`research-family.js` defines the reviewed `deor-feedback-v1` family in one place:
DEOR4 `[23,18,3,4]`, three key modes, two arithmetic directions, three reset
rules and the 55 nonempty raw LP2 pages 00–49 and 51–55. Every case tests the
same fixed Warning12 opening. This is 990 page/settings combinations, not 990
independent ideas, discoveries or published experiments. A matching prefix is
not a decryption; a mismatch excludes only that exact opening at that position.

The family revision binds the engine, input version, complete alphabet and
selected raw texts, key, allowed settings and criterion. Case IDs identify one
configuration and page within that revision. Presentation labels and map
placement do not determine coverage. Existing local-task identities are unchanged.

`createPreparer` validates and freezes source inputs once per request. Plans
contain at most twelve exact cases. Preparation does not execute manuscript
tests or create coverage. `family-runner.js` admits the complete plan and all
control suites before starting a fixed browser worker. All known-answer checks
finish before any manuscript case. Stopping discards the incomplete batch.

`family-runs.mjs` authorizes plans against the current official input bundle,
checks synthetic control witnesses, independently replays every target result
and atomically stores complete per-case evidence. Partial or tampered batches
save nothing. Duplicate submissions are idempotent. The server checks returned
calculations, not proof that a particular device physically performed them.

GET coverage checks saved task/result identities, full result digests and
prefix witnesses without re-executing targets. GET case evidence returns the
complete saved task, result and receipt. Coverage is revision-specific; a source
change does not silently apply earlier evidence to new text. The first version
conservatively starts a new family revision even if only one source page changes.

The workspace reviews a batch, runs locally, shows the result, saves only on
explicit action, then selects uncovered pages. Reload retrieves saved coverage
and complete outputs. Save failure retains local output for retry. The existing
Research map links to this workspace from feedback and repeating-key branches.
Historical prose and other prepared follow-ups are not automatically imported.

Limits are twelve cases per request, two MiB submitted JSON, the existing
per-client task limiter, and 1,000 newly stored family cases per day. D1 enforces
the daily limit inside the atomic transaction. This is a bounded first family,
not a general solution for large searches or distributed proof verification.

## Remaining cross-idea gap

Proposal identity currently hashes the complete standardized card, including
descriptive aim, labels and classifications. The relation matcher requires
these fields to agree before recognizing a page-scope variation. Community map
entries are projected per proposal. Consequently, alternate wording or placement
can still create separate cards for identical computations.

Do not solve this by erasing intent, making fuzzy matches authoritative, or
silently merging categories. Preserve proposal IDs as statements, task IDs and
receipts as immutable artifacts, and add a separate computation/evidence index:

- Exact engine, ordered operations, alphabet, input bytes and evaluation define
  executable equivalence. Labels, prose and map location do not.
- Additional pages add cases; overlapping inputs/settings can reuse witnesses.
- A changed criterion, key, reset, arithmetic or transcription changes the case.
- Missing settings remain unresolved, not wildcards. Unsupported methods retain
  separate statements until an execution adapter can establish equivalence.
- Multiple ideas and navigation placements may link to the same computation.
  Sharing a computation does not establish that it answers every linked aim.

The finite family's revision/case coverage is the first implemented instance
of this separation. General task deduplication, evidence reuse across family
definitions, compatible source-revision reuse, reservations for concurrent
visitors and automatic coverage of all map nodes remain incomplete.
