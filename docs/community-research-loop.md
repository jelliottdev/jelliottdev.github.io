# Community research loop

This is the implementation contract for the contribution workflow requested on
24 October 2026. All confirmed ideas use the same research-entry type. Input
that has not been confirmed is a draft, not a separate category of idea.
Original source wording is supporting material, not research-page copy.

## What a visitor does

1. Describe and confirm an idea using the existing standardized card.
2. Compare related work. A missing match is an archive gap, not proof of novelty.
3. Open the idea's research entry. See what is known, what remains untested, and
   which exact bounds can be extended. No second “suggest a test” form.
4. Review a prepared plan, then run it in the browser on the visitor's hardware. The plan
   states the method, scope, criterion, resource bounds and controls before the
   target run. AI may propose a plan; it cannot invent an executed result.
5. Inspect the local result, then submit it from the same page. A background
   Web Worker keeps the interface responsive and provides progress and Stop.
   Downloads and results-file uploads are optional reproduction tools.
6. The service checks the exact plan and independently verifies the results.
   The entry updates from the accepted data. Charts and counts use those data;
   nobody hand-edits a chart or writes a scientific outcome in advance.

## Separate identities and evidence states

An idea, a plan and a run are different objects. Keep the existing immutable
idea card and contributions; do not overload proposal review status.

- **Idea:** canonical active card, supporting original wording, candidate
  links to related records. Exact-card deduplication is not semantic novelty.
- **Plan:** immutable method, exact input text/alphabet, criterion and bounds.
  Its content digest changes when any of these changes. An extension references
  its parent and preserves the previous plan.
- **Run:** immutable returned outputs bound to that plan. Duplicate submissions
  reuse the same receipt, while independent contributions remain attributable.
- **Verification:** validator version and evidence checks. A valid file or hash
  alone is not scientific verification. Replay or check the actual witnesses.

Use user-facing states `Not run`, `Ready to run`, `Results submitted` and
`Results verified`. Verification means the stated computation was reproduced,
not that the cipher was solved. Incomplete runs cannot close an entire scope.

## Shared computation across idea entries

Navigation intent and executed work have separate identities. Two confirmed
cards may retain different wording, outcomes or map placements while requesting
the same computation. Keep those cards and their original task/result receipts;
do not copy a saved result onto another task or treat category changes as new
computational evidence.

`computation-evidence.js` derives a protocol identity from the engine, explicit
raw/reviewed input version, ordered alphabet, ordered steps and criterion. Each
page case additionally binds the exact page ID and text. Titles and page-batch
order do not change these identities. A different key, reset, criterion,
transcription or page text does. Reuse recognizes these exact supported protocols;
it does not infer mathematical equivalence, novelty or meaning from prose.

`task-evidence.mjs` finds saved results with a public idea association and the
same input version, conservatively requiring the source task's original input
version to agree too. Lookup checks immutable task/result identities and output
structure without decoding manuscript text again. Result admission remains the
independent replay performed when a result is submitted. A failed fixed-opening
test is still tested work; it is not an unrun case.

Coverage is the union of exact matching page cases, with links to their original
receipts. One compatible source covering the whole requested case set can be
opened directly. Partial coverage prepares only the remaining pages under the
same protocol, backed by pinned source receipts checked again at task creation.
The original confirmed card and its full intended scope remain unchanged.

`idea_computation_evidence` stores that complete frozen requested task and input
version, including requests with no current coverage. It stores no completion
flag. Reloading the idea recomputes coverage; the map/feed projects the latest
request and can show `Computation available` when even part has matching saved
work. That label neither claims complete coverage nor increases the idea's owned
task/result counts. Source discovery is bounded to 100 candidates and reports
truncation; missing evidence is not proof that work has never been done.

The finite family ledger uses family revision plus case ID. General discovery
now also reads validated `family_case_results`, returning `familySources`
metadata and links to revision-pinned family receipts. Conversely, the current
family snapshot reads exact compatible public general-task results. Both paths
preserve original tasks and receipts; neither copies results into the other
store. Family preparation rejects work already covered by either source.

The family snapshot still considers only its own current-revision family rows;
it does not scan earlier family revisions for unchanged pages. General idea
discovery can reuse an older family receipt when the requested protocol and
page bytes match exactly. The historical case route pins the saved revision
rather than substituting the current input snapshot. Reviewed prose records
are not automatically imported, and no concurrent work reservations exist.

## Evaluation must match the intended question

A deciphering outcome with no specific evaluation is a clarification state,
not permission to substitute descriptive statistics. Intake offers a maintained
choice between readable-text evaluation, the exact 12-rune Warning opening,
and explicit output inspection. Each choice preserves the original aim and
source. Specified criteria are not replaced. Explicit inspection may report
counts, but does not judge readability. Readable-text evaluation currently
requires an adapter and cannot silently become inspection or a prefix test.
The backend checks this before AI mapping, input loading or task creation;
older saved ideas receive an inline path back to review.

The current family also has a necessary-condition filter. `proveCaseExclusions`
checks the first output rune against the fixed opening without decoding the
page. Excluded cases retain their identities and previous saved runs, but are
not offered as new work. They are deductions under this exact family and opening,
not saved computations or exclusions of other plaintext. With the current raw
inputs, 963 of 990 cases fail this condition and 27 survive it. Surviving a
necessary condition is not a match. Browser and server independently apply the
filter; preparation rejects excluded cases before controls or manuscript runs.

## First execution contract

`local-experiment.js` is the shared, deterministic validator/evaluator.
`local-run-worker.js` runs the site-owned engine in a browser Web Worker;
`local-run-executor.js` manages its progress, cancellation and deadline.
`tools/research_runner.py` optionally reproduces the same task without network
access or extra Python packages. None executes visitor code or text as instructions.

The `liberpedia-local-task-v1` format contains the complete inputs and ordered
steps. `taskId` is SHA-256 of canonical sorted compact UTF-8 JSON, excluding
`taskId`. The task contains an explicit ordered 29-rune alphabet, up to75 pages,
20,000 runes, and eight steps. The `rune-program-v1` engine initially supports:

- Reversal inside each page, line or visible word, retaining separator positions.
- An explicit affine map on rune indices modulo29.
- Cumulative difference `P[k] = C[k] − sum(P[0..k−1]) mod29`, with a declared
  page, line or word reset and zero initial state.
- Finite streams of explicit GP indices, with no wrapping or inferred continuation.
  Each complete reset segment must fit the key before execution. Standardized
  card size limits remain distinct from engine limits.
- Keyed shifts with an explicit seed of 1–256 GP indices (0–28), add/subtract
  decoding direction, and page, line or word reset. The key can repeat, extend
  from decoded runes (plaintext autokey), or extend from input runes (ciphertext
  autokey). Non-rune characters do not advance the key. Every page starts fresh;
  a request to carry state across pages is not represented by this operation.

A complete canonical `interrupted_repeating_key` operation also supports literal
interruptions of a repeating key. Its explicit `interrupts` list contains sorted,
unique GP indices. On those current-step input runes, copy the rune unchanged and
hold the key position; decode all other runes normally and advance the key. This
is different from decoding a marker while only pausing its clock. Reset remains
explicit per page, line or word. No feedback/autokey mode is implied. Unsupported
free-text mappings remain unresolved rather than becoming ordinary Vigenère.

This literal interruption map is not always invertible. An expected non-marker
rune may require an input marker, which the operation would instead copy. The
synthetic control constructor rejects such an unreachable known plaintext; it
must not alter the key, criterion or expected text to manufacture a passing
control. A supported operation alone does not make a published follow-up ready.

Autokey uses the seed first, then the rune one seed-length earlier in that step's
decoded or input stream. `add` means `P = C + K`, not an alternative encryption
API. A compound method uses each step's own input and output, not the untouched
manuscript. The independent Python runner and browser engine share these exact
semantics. Legacy task identities and results retain their original meaning.

These are execution primitives, not a claim that all earlier experiments or
arbitrary new methods are supported. Keyword-to-rune encoding, prime values,
alternate alphabets, skipped
runes, language models and other operations need explicit versioned adapters.
Never silently approximate an unsupported instruction. Preserve it in planning.

The criterion is a measurement (no success/failure verdict), a fixed within-word affine-pair count with exact conditional expectation, or an exact rune-index prefix fixed before the run. Matching a prefix is not decryption.
The output includes transformed text, pooled IoC, rune counts and repeat counts. The word-pair criterion adds per-page and aggregate pair counts with exact rational expected values; it does not assign a significance level or reproduce a full affine-map search.
Repeat counts use consecutive runes after removing separators, separately on
each page; they do not claim to be within-word doublet counts.

The verifier reruns the bounded computation and compares every output, rather
than accepting uploaded totals, `PASS`, HTML, scripts or a claimed environment.
The displayed summary and chart data derive from the verified result. A result
must remain bound to its input text; browser/Worker code must fetch and pin the
site's authorized text version before calling a task manuscript evidence.

## Research entries and supporting material

There is one research-entry type, with no visibility settings or private/public
categories. Confirming a card adds the entry to the shared research collection.
Before confirmation, the input is a draft. Original pasted wording remains
supporting intake rather than page copy.

### Extending a test

The task workspace offers a system-defined scope extension to the remaining
unsolved LP2 pages (00–55). Planned page scope and saved result coverage are
separate. An unfinished current or compatible ancestor experiment is linked for
completion before proposing more pages. A local-only result does not advance
saved coverage. Redundant pending work is suppressed only when a saved compatible
run covers the same page IDs and exact input text. It proposes a
separate child computation with the same ordered method, alphabet, input version
and criterion. The page list is reviewed before creation; no extension runs or
submits itself. The original card and earlier result stay unchanged. This is an
explicit expansion beyond the original request's pages, not a claim that those
pages were previously covered. Existing identical computations are reused.

`POST /tasks/:id/extensions` prepares this scope without writing a task, fetching
only fixed official page sources. The ordinary task and result routes create and
verify the reviewed computation. Missing or redirected source data cannot produce
an accepted plan. Unsupported methods are not approximated by the extension.

Persistent entries, task plans and replayed results use their own storage and
API, linked to the existing proposal identity. A result is local until the
submission receives a valid saved receipt. Do not present a browser-only run
or local file verification as a stored/public contribution.
Do not expose private source wording when projecting an idea to a public entry.

Prepare plans from reviewed execution adapters. AI selects and fills supported
parameters under the same strict validator; unsupported plans stay unresolved.
Plan generation has bounded requests, rate limits and no arbitrary fetch/exec.

Publish accepted execution evidence through the existing one-file experiment
compiler. Keep an untested task distinct from a completed research record. Update
the Research map from those states, with related/parent links and precise tested
bounds. AI prose is optional explanation; typed verified evidence determines
counts, charts and the limited outcome.

## Required end-to-end proof

Before calling the loop complete, demonstrate a new confirmed idea creating a
persistent entry; a fixed plan run in a real browser Web Worker; honest
output accepted and tampered output rejected; a reload retrieving the receipt
and chart; a changed scope creating an extension without overwriting the earlier
result; repeat submission deduplicated; failures preserving inputs; and mobile
navigation between the checker, task and research map; and the optional downloaded
package independently reproducing the same computation. Use local fixtures before
any hosted generation. The runner foundation alone does not complete this loop.

## Remaining requirements

The map is not yet an execution interface for every node. Published records and
method branches still need structured tested bounds, explicit open variants and
links to prepared runnable plans. Narrative exclusions alone do not define an
exhaustive complement, and a browser measurement does not test an arbitrary
solving hypothesis. Evaluation adapters with declared success criteria and
positive/negative controls remain required for that broader workflow.

### Controls for descriptive follow-ups

An authored measurement can use a synthetic exact-prefix control with the exact
same ordered steps and alphabet. Its known answer checks implementation of the
method; it is not a plaintext criterion for the manuscript. Both complete task
identities and the complete synthetic result digest remain mandatory. A generic
measurement control cannot certify itself through an empty success condition.
Existing exact-prefix and word-pair tests still require identical control and
target criteria. The controls run before any manuscript computation. Findings
for a descriptive target remain measurements, with no readability verdict.

### Authored language comparisons

Use `scripts/browser_followups.py::construct_language_followup` to author a
fixed comparison once. It accepts explicit operations, pages and independently
specified synthetic input/output. The maintained three-field `language-score`
criterion is pinned; custom models, thresholds and unrecorded search settings
are rejected. A source should explain why these exact settings are worth
checking and distinguish an extension from its earlier tested bounds.

The full synthetic output verifies the transformation. Two independently
calculated runner checks verify the language arithmetic before target pages run.
Neither requires readable output or a high language score. Browser execution,
remaining-page execution, saved charts and offline reproduction retain both
checks and the same model identity. Ordinary measurement checks do not download
the model. The offline authored command is `verify_authored_language.py`; exact
remaining-page packages retain `verify_subset_controls.py` and include the model.

This adapter supports fixed plans, not an inferred exhaustive parameter family.
Do not split every key phase into separate research records or claim a language
comparison establishes decipherment. A complete finite family still needs its
explicit case definition and evidence for every claimed case.

### Word prime-value ledgers

`word-prime-sums` measures word values without claiming a decoding rule. It uses
canonical GP prime assignments or reverses the actual ordered 29-value table
(F=109, U=107, through EA=2). This is not decimal-digit reversal, an emirp rule,
or subtraction from a fixed constant. Word grouping must explicitly choose
non-rune boundaries or the earlier hyphen/period convention; pages stay separate.
The output retains each measured rune group and its exact total. The shared
view exposes bounded page/word browsing and a calculation from the actual data.

A synthetic ledger control uses the identical table and grouping rule and a
complete expected result digest. Direct sums do not reproduce a prime-excess
permutation test, candidate-key collision study or a readable-text test. Changing
the table in such a study also changes its controls and target values; the
original findings cannot be inherited from this ledger.


### Clarifying a word-sum idea

The intake recognizes only complete positive instructions to reverse the GP
prime table and sum words. It asks for aim and scope first, then an explicit
word-break choice. The choice also confirms the archived rune input and the
reversed prime assignment. The canonical operation and numeric evaluation are
created only after that answer, before confirmation and storage. Choosing to
keep the original wording does not silently select a boundary rule.

Negations, conditions, appended methods, conflicting value examples and existing
rule conflicts remain opaque. Existing confirmed cards are never rewritten.
The adapter changes neither the visitor's outcome nor page selection. Its result
is a word-value ledger, not a readability test or statistical explanation.

## Automatic implementation checks

Generic plans now use `local-plan-controls.js` to derive two small synthetic
fixtures from the exact ordered program. A separate reference implementation
calculates the complete expected outputs before comparing them with the runner.
These checks do not run manuscript inputs, infer a plaintext, measure a false
positive rate or validate a proposed cipher model. Finite keys may restrict the
available synthetic segments. Prefix checks use a known synthetic match and a
mismatch; they do not supply the target's unknown answer.

The proposed plan and task view expose the target-bound checks. The browser
rederives them, runs them in its cancellable worker before manuscript pages and
requires both complete result hashes to match. The service independently
rederives/replays generic checks before task creation, result acceptance and
saved-result verification. Authored follow-ups retain their own stronger,
source-bound controls. Existing task and result identities remain unchanged.

Optional generic downloads include `runner-controls.json` and
`verify_plan_controls.py`. The independent Python runner checks both synthetic
outputs before the target and refuses to overwrite results. Existing three-file
replay downloads and authored-control packages remain supported.

A matching implementation check verifies the stated arithmetic on small inputs;
it does not establish readability, statistical significance or complete coverage.

### Remaining loop boundaries

Generic tasks require a server-issued preparation binding the original idea,
exact program, criterion, input version, parent and known-answer controls.
Validated AI mappings and supported extensions preserve their separate basis.
Existing tasks remain retryable without changing their original evidence.
Extensions cover remaining LP2 pages and fixed word-boundary comparisons,
not arbitrary parameter sweeps.
The existing global daily persistence caps also remain in place. These gaps mean
the full contribution loop is not complete for every idea or research node.


### Comparing word boundaries

Completed word-prime-sum and within-word affine-pair measurements can prepare a
second run that changes only how words end: either every non-rune ends a word,
or only ASCII hyphens and periods do. Both use the exact same saved page text,
alphabet and other measurement settings; transformed text is excluded. The
original idea and result remain unchanged. A saved parent is required before
creating the comparison, and an existing matching task is reused.

Review and creation remain explicit. After the comparison runs, show the two
results side by side: group counts and assigned totals for sums; matching and
eligible pairs for the affine measurement. Neither rule is pronounced correct,
and these differences do not establish a cipher. Scope extensions and boundary
comparisons have different preparation authorities and cannot impersonate each
other. No AI chooses a new boundary rule or writes a result.


### Shared protocol definitions

`experiment-protocols.js` is the common description of the word-prime-sum and
within-word affine-pair protocols: accepted method parameters, named settings,
canonical task titles, plain questions, instructions, limits and supported next
changes. The planner, authored follow-up validator and browser workspace use
these definitions. The word-boundary variation uses the same settings and
allowed choices, rather than maintaining a separate version of each method.

Protocol descriptions do not calculate answers or certify scientific outcomes.
The JavaScript evaluator, independent Python runner and synthetic known-answer
controls remain separate implementations. Existing task titles, identities,
criteria and results retain their meaning. New numerical methods still need an
explicit evaluator and independent verification; a metadata entry alone cannot
make arbitrary ideas executable.

This is the first migrated branch, not a claim that all published records now
have structured executable bounds or that every open setting is a runnable
follow-up. Expanding the catalog requires both executable support and a stated
question, evaluation and limit.


### Discovering available work

The research map uses its existing filter for two different work states:
prepared published follow-ups (`followups=1`) and saved unfinished experiments
(`followups=pending`). Graph and List keep the same current branch and matching
records. Prepared work may already have a saved result. Unfinished means a
registered task has no accepted result; an idea with no task is not advertised
as ready to run.

`research-work.js` classifies the currently loaded snapshot from validated
follow-up declarations and exact community task counts. Its counts describe
individual records or ideas, not unique computations across the archive. The
community feed prioritizes unfinished summaries within its ten-task projection
so older unfinished work remains directly reachable. Overall community loading
and pagination remain separate, and missing pages or a service error cannot
establish that no unfinished work exists.


### Linked questions and completed results

A published record can declare optional `research_questions` in its single
`record.json`: 1–12 objects with `id`, `question`, `state` (`tested` or `open`),
`note`, and `records` (other published record IDs). Notes explain what the linked
results answer, including their limits; open questions can have no linked record.
The research map and library reuse that source rather than authoring separate
coverage summaries.

Question state is an explicit editorial judgment. Neither AI matching, similar
wording, a saved computation nor a new published result automatically closes a
question. `tested` is not proof or universal coverage, and `open` is not a claim
that a browser plan exists. Runnable follow-ups remain separate validated
declarations. When evidence changes, update the originating question and its
links deliberately, preserving the historical experiment and its exact bounds.

An optional `followup` names one existing browser recipe owned by the same record.
An open question links to plan review; a tested question links to reproduction
and must also cite the completed evidence in `records`. A recipe may appear in
only one question, so conflicting open/tested states are rejected. These links
do not change the pinned recipe or task identity. `record-question-model.js`
provides the common question state used by the record view, recipe actions and
available-work filter. Tested reproductions remain directly accessible but are
not counted as new prepared follow-up work.
