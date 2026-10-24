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
- Keyed shifts with an explicit seed of 1–256 GP indices (0–28), add/subtract
  decoding direction, and page, line or word reset. The key can repeat, extend
  from decoded runes (plaintext autokey), or extend from input runes (ciphertext
  autokey). Non-rune characters do not advance the key. Every page starts fresh;
  a request to carry state across pages is not represented by this operation.

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

The criterion is either a measurement (no success/failure verdict) or an exact
rune-index prefix fixed before the run. Matching a prefix is not decryption.
The output includes transformed text, pooled IoC, rune counts and repeat counts.
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
