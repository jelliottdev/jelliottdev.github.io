# Community research loop

This is the implementation contract for the contribution workflow requested on
24 October 2026. It supersedes the earlier rule that all new ideas remain only
in a private maintainer queue. It does not change the status of existing ideas
or publish their original wording.

## What a visitor does

1. Describe and confirm an idea using the existing standardized card.
2. Compare related work. A missing match is an archive gap, not proof of novelty.
3. Open the idea's research entry. See what is known, what remains untested, and
   which exact bounds can be extended. No second “suggest a test” form.
4. Review a prepared plan, then download its runner and fixed inputs. The plan
   states the method, scope, criterion, resource bounds and controls before the
   target run. AI may propose a plan; it cannot invent an executed result.
5. Run locally, then return the results file. Failure leaves both the entry and
   the local output recoverable.
6. The service checks the exact plan and independently verifies the results.
   The entry updates from the accepted data. Charts and counts use those data;
   nobody hand-edits a chart or writes a scientific outcome in advance.

## Separate identities and evidence states

An idea, a plan and a run are different objects. Keep the existing immutable
idea card and contributions; do not overload proposal review status.

- **Idea:** canonical active card, retained original wording privately, candidate
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
`tools/research_runner.py` runs the same task without network access or extra
Python packages. Neither executes generated code or text as instructions.

The `liberpedia-local-task-v1` format contains the complete inputs and ordered
steps. `taskId` is SHA-256 of canonical sorted compact UTF-8 JSON, excluding
`taskId`. The task contains an explicit ordered 29-rune alphabet, up to75 pages,
20,000 runes, and eight steps. The `rune-program-v1` engine initially supports:

- Reversal inside each page, line or visible word, retaining separator positions.
- An explicit affine map on rune indices modulo29.
- Cumulative difference `P[k] = C[k] − sum(P[0..k−1]) mod29`, with a declared
  page, line or word reset and zero initial state.

These are execution primitives, not a claim that all earlier experiments or
arbitrary new methods are supported. Prime values, alternate alphabets, skipped
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

## Service and publication boundary

Persistent tasks, plans, runs and verification receipts still need their own
storage and API, linked to the existing proposal identity. Do not present a
browser-only download or local file verification as a stored/public contribution.
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
persistent entry; a fixed plan downloaded and run in an isolated folder; honest
output accepted and tampered output rejected; a reload retrieving the receipt
and chart; a changed scope creating an extension without overwriting the earlier
result; repeat submission deduplicated; failures preserving inputs; and mobile
navigation between the checker, task and research map. Use local fixtures before
any hosted generation. The runner foundation alone does not complete this loop.
