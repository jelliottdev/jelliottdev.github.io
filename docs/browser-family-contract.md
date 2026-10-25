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
prefix witnesses without re-executing targets. It combines the current revision's
family rows with exact compatible public general-task results. GET case evidence
returns the original saved task, result and receipt. A general-task source uses
the typed `source:{task,inputVersion,run}` response; it is not relabeled as a new
family run. Preparation rejects cases already covered by either source.

The family's own ledger remains revision-specific. Changing even one selected
source page starts a new revision, and the snapshot does not scan older family
revisions for unchanged cases. General task evidence can still contribute when
its exact page and protocol match the current inputs.

The workspace reviews a batch, runs locally, shows the result, saves only on
explicit action, then selects uncovered pages. Reload retrieves saved coverage
and complete outputs. Save failure retains local output for retry. The existing
Research map links to this workspace from feedback and repeating-key branches.
Historical prose and other prepared follow-ups are not automatically imported.

Limits are twelve cases per request, two MiB submitted JSON, the existing
per-client task limiter, and 1,000 newly stored family cases per day. D1 enforces
the daily limit inside the atomic transaction. This is a bounded first family,
not a general solution for large searches or distributed proof verification.

## Two-way shared evidence

Proposal identity hashes the complete standardized card, including descriptive
aim, labels and classifications. Those cards remain distinct statements of
intent. `computation-evidence.js` separately identifies exact protocols and page
cases, allowing different cards or map placements to share execution evidence.

Preserve proposal IDs, original task IDs and immutable receipts:

- Exact engine, ordered operations, alphabet, input bytes and evaluation define
  executable equivalence. Labels, prose and map location do not.
- Additional pages add cases; overlapping inputs/settings can reuse witnesses.
- A changed criterion, key, reset, arithmetic or transcription changes the case.
- Missing settings remain unresolved, not wildcards. Unsupported methods retain
  separate statements until an execution adapter can establish equivalence.
- Multiple ideas and navigation placements may link to the same computation.
  Sharing a computation does not establish that it answers every linked aim.

`family-shared-coverage.mjs` imports no results. It reads validated public general
task receipts into the current family snapshot, matching raw input version,
ordered alphabet, steps, criterion and exact page ID/text. Matching and failed
Warning openings both cover their cases; the matched subset remains explicit.
The lookup uses eighteen indexed protocol queries, at most 100 source tasks per
configuration and 16 MB total. Exceeding a limit or finding conflicting evidence
fails explicitly. Reading one shared case returns its original general receipt.

In the other direction, `family-evidence.mjs` supplies validated family receipts
to general task discovery. `familySources` identifies their family, revision and
case without copying a result into `local_task_results`. A pinned
`GET /families/deor-feedback-v1/cases/:caseId?revision=:revision` opens the saved
historical family receipt, including after the official input snapshot changes.
General discovery may reuse a historical family page only when its exact text
and protocol match the requested computation. That does not make the current
family snapshot scan older revisions automatically.

Partial general requests keep their full intended scope and prepare only pages
not covered by original pinned receipts. Unsupported protocols and missing
settings are not equivalent by inference. Historical reviewed records are not
automatically imported. Reservations or concurrent leases are not implemented:
two visitors can prepare the same open work before either saves it, although
saved duplicate submissions remain idempotent. Automatic coverage and execution
for all map nodes remain incomplete.
