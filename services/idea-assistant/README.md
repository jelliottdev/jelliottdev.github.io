# Hosted idea comparison

## Browser experiment loop

The new `/tasks` routes link a confirmed idea to an immutable declarative plan,
then accept submitted results only after replaying the bounded computation. The
handler verifies bundled page text against the site's selected raw or reviewed
text. Task and result storage are separate from proposal review status; neither
the original idea wording nor private notes appear in task projections.

Storage migrations 0004–0006 were applied on 24 October 2026. Production checks
verified official-source loading, source-bound compound and explicit numeric-key
plans, and replayed result storage. Synthetic checks did not create shared research entries. Local
browser fixtures verify the visitor workflow; these checks do not establish the
quality of arbitrary model interpretations or a scientific finding.

The checker publishes only a newly confirmed active card through `/ideas`, then
links to `run.html#idea=…`. The original submission text remains in private intake.
There are no private/public idea types or visibility settings: every confirmed
research entry is shared. Unfinished intake is not a second kind of idea. A task
view uses a saved entry's card and association metadata, rather than exposing an
unpublished intake card when a computation is reused.
The run workspace reviews a proposed plan, creates a task, runs it on the visitor's
CPU in a cancellable Web Worker and submits replay-checked results. Downloads and
file uploads are optional reproduction paths. The result and dynamic chart lead;
exact plan details remain available after a run.

`POST /tasks/:id/extensions` proposes the same computation on remaining unsolved
LP2 pages. Compatible ancestor scopes are retained so a child does not offer its
parent's pages again. Review and task creation are explicit; neither overwrites
an earlier task. The result inspector displays one page's original and transformed
text at a time, with rune-label transliteration clearly separate from translation.

`/prepare-task` first checks explicit supported operations with the deterministic
compiler and complete method phrases using a closed grammar. Exact supported
phrases do not require a model call. If compound wording needs mapping and an AI
binding is available, one model request may propose exact source spans for the reviewed primitives: rune
reversal within a line, word or page; an affine index mapping with explicit
parameters; cumulative difference with an explicit reset; or repeating keys and
plaintext/ciphertext autokeys with explicit GP indices, direction and reset. A closed local
grammar checks every phrase and accounts for all method wording. The deterministic
compiler then checks the complete proposed plan. The model cannot supply code,
invent keys or page selections, discard conditions, or decide the result.

The original confirmed card stays unchanged. Proposed interpretations and defaults
are shown for review before creating the task. Missing exact scope, unresolved
conditions and unsupported methods remain `needs-adapter`; a deciphering goal does
not turn a measurement plan into a readability test. The optional mapper makes at
most one generation per explicit preparation, with a 20-second response deadline,
three concurrent calls per isolate and a bounded exact-card cache. A timed-out
provider occupies its slot until it actually settles. No automatic repair or retry
is performed. This is bounded planning, not automatic execution of arbitrary ideas.

No download, Python installation or uploaded result file is needed for the normal
flow. The site's fixed browser engine runs the approved plan in a cancellable Web
Worker. Submitting its output is a separate action. The server
replays that exact task before storing a content-addressed receipt; the result and
chart mean **verified computation**, not a correct reading, a language verdict or
exhaustive coverage of a cipher family. Community run state remains separate from
published scientific records and proposal review decisions.

`local-experiment.js` and `tools/research_runner.py` share the execution contract.
`local-run-view.js` renders its result and chart directly from verified data.
See [the loop contract](../../docs/community-research-loop.md) for required
states, exact bounds, unsupported methods and the end-to-end acceptance proof.
Offline checks from this directory:

```text
node test-local-tasks.mjs
node test-prepare-task.mjs
node test-propose-task-plan.mjs
```

These use real local SQLite with injected page/provider fixtures, without hosted
model calls. From the repository root, `python scripts/test_research_runner.py`
checks the optional external runner. Passing mocks verifies the contracts; it is
not evidence of live model mapping quality.

## Optional interpretation endpoint

The `/interpret` route is enabled through `interpretationEndpoint` in
`data/assistant.json`. It runs only on explicit idea submission. Visitors review
the proposed card before comparison; local clarification remains available if
interpretation fails.

The endpoint proposes a source-bound draft using a strict model wire schema,
then validates the converted candidate with the same browser/Worker code. It
never confirms an idea, executes a test, or saves a proposal. Unique exact quotes
can have their character positions corrected; their wording and meaning fields
cannot be repaired. The source-only wire format supplies complete instruction
quotes; the adapter derives literal keys and page lists from those quotes.
Null aims and an empty rules array preserve missing information. Explicit rule
states require wording about the named rule. Invalid output returns a recoverable
error. Literal key contents cannot serve as outcome, page or rule evidence.

24 October 2026: deployed source-only extraction and the shared outcome-evidence
gate as Worker version `7564f79f-305b-45a0-9f53-8f9c8e99a527`. A production synthetic
measurement request preserved its explicit aim, ordered instructions, page-list
gap and 2,000-shuffle control. Four captured responses also replay correctly:
measurement, ordered methods with a literal key, an excluded page, and a method
without an aim. The last now asks for an aim instead of assuming deciphering.

Verification includes 24 mocked handler groups, 20 shared-validator groups,
26 synthetic candidate cases, six browser parity groups and UI journey tests.
These do not establish complete extraction accuracy. Unsupported aim wording
stays undecided; original wording remains visible for review. Confirmed ideas
use the separate storage endpoint described below.

One uncached interpretation makes one generation, with no automatic repair or
retry. A 20-second response deadline, three active provider slots per isolate,
the existing rate-limit binding, exact-input cache and singleflight bound work.
A timed-out generation retains its slot until the provider settles. These are
not a global daily quota. See `docs/frontend/claim-specification.md` for the
review contract and `test-interpret-handler.mjs` for offline verification.

24 October 2026: deployed the plural-row clarification validator as Worker version
`cb302f9b-0731-4d73-a986-4a99d200c41d`. The exact phrase “Reverse prime values in
rows” retains its ambiguity for user clarification. Offline Worker and browser
validator checks reproduce the former rejection and verify the correction. No
model generation was needed for this deployment check.

## Confirmed idea storage

The `/proposals` endpoint stores the confirmed standardized card and its original
wording in a private D1 review queue. Confirmation is the only visitor action
needed; there is no separate test-submission form. A receipt means the idea was
received, not that its novelty was established or an experiment was published.
Maintainers compare overlap and decide what needs testing using
[`REVIEW-PROPOSALS.md`](REVIEW-PROPOSALS.md).

Worker version `7921b397-10f7-4510-bbc3-3ee5896a6e61` binds `PROPOSALS` and a
separate three-per-minute intake rate limit. All three schema migrations were
applied. On 24 October 2026 two identical synthetic requests returned `received`
then `already_received`, with the same receipt; the database contained one card
and one submission with the original wording intact. The synthetic card was
declined with an audit reason so it is not queued as research. These checks used
no model generation.

The browser retains one bounded intake body in session storage for up to 24
hours. After a refresh, explicit reconfirmation retries its original request ID
when the wording and card are unchanged. Stored receipts are rechecked with the
server. Nothing is submitted just by restoring a draft or opening a shared link.
Edited wording or a changed card creates a new request. Exact-card deduplication
is storage behavior, not semantic novelty detection.

## Comparison endpoint

This replaces the browser model download. Visitors submit the same idea-search form; the page shows retrieved records immediately and adds a short cited comparison when the service is available. There are no model controls, visitor accounts or API-key fields.

Production endpoint: `https://liberpedia-ideas.josephelliott127.workers.dev/ask`. Workers Free was verified in the dashboard before deployment.

## Deploy once

1. Use a Cloudflare account on **Workers Free**, not Workers Paid. The free plan currently includes 10,000 AI neurons per day. Once exhausted, AI calls fail rather than incur paid overage. Do not upgrade or attach paid AI Gateway credits as part of this setup.
2. From this directory, run `npx wrangler login`, then `npx wrangler deploy`. Login uses browser OAuth; no provider API token is needed. Alternatively deploy through Cloudflare's Git integration using this directory and config.
3. Verify the deployed `/ask` endpoint with the Liberpedia Origin header. With an empty registry it must return `no-matching-records` without calling a model.
4. Set `data/assistant.json` to `{"endpoint":"https://YOUR-WORKER.workers.dev/ask"}` and publish the wiki. Leave it null until deployment is verified. The value is public and is not a credential.

The configured model is `@cf/google/gemma-4-26b-a4b-it`, currently available on Workers Free. Model availability can change; verify the official catalog before deployment.

`AI` is a Cloudflare binding, not a secret. No OpenAI, Anthropic, or visitor key is required. A Cloudflare account and one-time deployment are still necessary. The browser communicates with an HTTP endpoint; “no keys” does not mean there is no network API.

## Behavior and limits

The Worker retrieves the public experiment registry and a compact supporting-page index, cached for five minutes. It ranks **techniques first**, after removing page references from the query. A page match alone never triggers inference. Selection retains complete experiment scopes and up to two relevant excerpts from explicitly named pages. Confirmed compound methods can select up to four experiment records within the same evidence budget. Page evidence is supporting context, not evidence of a test. Retrieval is lexical, not an exhaustive semantic or novelty check.

Concurrent cold requests share one index load. A failed or malformed optional supporting-page index leaves the experiment records usable; a failed experiment registry still stops comparison rather than substituting page context for evidence. The next load after the five-minute expiry picks up published record changes. Loader tests simulate refreshes, failures and recovery without network access.

Only published experiment records are eligible. Empty registries, page-only requests and unmatched techniques do not spend inference. Experiment scope is never silently truncated to fit a prompt. The strongest match must fit the 9,000-character experiment allowance; a second match is included only if both fit. If the second cannot fit, the first remains usable and the ordinary result list still exposes the other records. An oversized strongest match stops inference rather than substituting a weaker match. Total context is bounded to 11,000 characters and output to 700 tokens (requested prose: normally 60–120 words, at most 180 for compound methods). Thinking is disabled. Citations are checked for valid source numbers, which does not prove factual entailment. Markdown rendering escapes HTML and only links to evidence-owned wiki routes.

Repeated requests reuse answers in three ways: a bounded browser-memory cache (20 entries, one hour), bounded Worker memory (100 entries, one hour), and the Cloudflare Cache API (up to 24 hours). Cache keys hash the exact whitespace-normalized question, selected pages, evidence contents, model and prompt version; case is preserved for cryptographic questions. Changed evidence invalidates an answer. Edge cache entries are local to a Cloudflare data center and may be evicted; this is not a global or guaranteed hit rate. Equal concurrent requests share one inference within an isolate. Three concurrent generations per isolate and a 60-second outage cooldown reduce retry storms; these are not account-wide limits.

The browser only requests inference on explicit submission when related experiments exist. It does not call the model on keystrokes, route opening, page selection, or ordinary wiki navigation. Repeat submission is disabled while waiting. Stopping the wait cancels the browser request but cannot promise to cancel already-started inference or refund quota.

The configured rate limit permits six requests per minute per IP at a Cloudflare location. This is not a global quota or a guarantee against abuse; Origin checks are also not authentication. Workers Free provides the cost ceiling. Anonymous public access can exhaust the free allowance, in which case source records remain usable. No automatic paid fallback is configured.

Questions and retrieved text are sent to Cloudflare. The Worker does not log request bodies; observability is disabled. Answers and their source excerpts are temporarily cached and can be reused for the same question. The cache URL contains a SHA-256 digest, not the question; generated answer text can nevertheless reflect the submitted question. The form advises users not to include private information, and the coverage disclosure explains reuse. Cloudflare's service policies still apply.

## Validation

20 October 2026: deployed technique-phrase retrieval as Worker version `37f91740-5c46-422b-82ee-711aa91f493b`. Complete multiword tags receive a bounded, non-stacking phrase boost; incidental conversational terms no longer dominate the language-comparison question. The same retrieval module serves browser and Worker. Current-record tests use mocked inference, including the full different-language question. No hosted generation was used.

20 October 2026: deployed bounded best-match retention as Worker version `f5599f8a-5d78-4ee9-a463-bad662ad48fb`. The new segment-order record exposed a pair of complete scopes exceeding 9,000 characters. Tests now verify retaining the strongest whole record, refusing an oversized strongest record, and limiting supporting page excerpts to two. Published-record handler tests pass with mocked inference; no hosted model request was made.

20 October 2026: deployed optional-context failure handling and shared index loads as Worker version `4cb2c95a-8273-4480-a1ae-46eaffdfcde2`. Mocked tests cover current published records, complete evidence preservation, five-minute refresh, load failures and retries. Wrangler confirmed deployment with the existing AI and rate-limit bindings. No hosted inference request was made for this deployment; it is not a new model-quality evaluation.

Run `node services/idea-assistant/test-worker.mjs` and `node scripts/test_assistant.cjs` from the repository root. Tests use a fake inference binding and never consume hosted quota. Complete a real deployed integration check before enabling the endpoint. Do not call the hosted assistant operational while `endpoint` is null.

One remote synthetic-fixture smoke test on 19 October 2026 used one model generation: approximately 3.3 seconds cold and 0.7 seconds for a cached repeat. The answer correctly distinguished one synthetic row from all manuscript rows. This is not a latency benchmark or an evaluation on real experiment records. The public registry remained empty.

Official documentation checked 19 October 2026:

- [AI bindings: no secret keys required](https://developers.cloudflare.com/workers-ai/configuration/bindings/)
- [Free allowance and hard limit](https://developers.cloudflare.com/workers-ai/platform/pricing/)
- [Cache API and data-center locality](https://developers.cloudflare.com/workers/runtime-apis/cache/)
- [Rate-limit binding](https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/)

Puter requires visitor sign-in and uses visitor allowances/billing. Pollinations generation now requires keys. Neither meets the requested friction-free visitor experience as directly as a hosted binding on the free plan.

Record-type labels and definitions travel inside each complete research excerpt. The checker sends matching methods, replays, measurements and controls to inference, while keeping their types explicit. An exact measurement can answer whether a pattern was tested without being described as a solve attempt. A source audit can supply supporting evidence when the query names its checked operation and it strongly outranks incidental test matches; a bare artwork or page mention does not trigger inference. Audits remain distinct from solving tests. Prompt version `research-v7-typed-records` invalidates earlier answer caches; exact evidence changes also invalidate them.

23 October 2026: deployed authored-method retrieval and typed citations as Worker version `4c6de8eb-0e5b-48ee-90c7-fce4154dac2d`, after the 263-record registry published at commit `0537ba42a7fe152920e95ea030689aa40326ad01`. Named autokey proposals no longer yield to incidental motif prose; precise lag-six measurements retain priority over broad method aliases. Browser and Worker use the same selector and complete evidence budgets. Mocked inference suites, generated-registry regressions, CORS preflight and a deployed page-only no-match check passed. No hosted generation was used for this deployment.


24 October 2026: deployed the confirmed-idea context contract as Worker version `49ea3923-4991-4ed9-bf8e-38cd7bc0350e`. A concise `query` (up to 1,500 characters) drives retrieval; optional `confirmedQuery` (up to 6,000 characters) supplies the full interpretation and original wording to the comparison. The request body is capped at 32,000 bytes. Missing parameters remain unknown. Cache version `research-v8-confirmed-context` includes the exact confirmed context as well as selected evidence. Existing query-only clients remain supported. Mocked tests cover retrieval isolation, context-sensitive caching, and input bounds; the deployed page-only no-match check returned without inference. No hosted generation was used.

The comparison uses the confirmed aim as well as the procedure and scope. The response explains the closest usable finding, the difference that matters, and only a justified next action. Reusing saved output, recovering a missing input and checking reproducibility are distinct from a new experiment; a next step is optional. Prompt changes invalidate the answer cache. No extra inference call is used for these presentation changes.

24 October 2026: deployed this response guidance as Worker version `ef98e2a1-b9c9-46ee-9b78-acd7a66f44fd`, with cache version `research-v9-decision-value`. Mocked inference tests pass; deployment retained the existing AI and rate-limit bindings. No hosted generation was used, so this is not a live model-quality evaluation.

24 October 2026: shared outcome and method-family vocabulary is grouping metadata, not experiment identity. The comparison must retain exact scope, settings and success criteria, including the difference between a readable passage and a complete solution. Unknown wording does not create a category. Deployed as Worker version `5cce2941-34ce-4823-a383-3b584529aca2` with cache version `research-v10-shared-outcomes`; mocked tests pass and no hosted generation was used.


## Findings and comparison are separate

The standalone checker displays each selected experiment’s authored finding and
limit before the AI explanation. These come from the exact validated evidence
text, including optional `reader_finding` and `reader_limit` fields; they are not
regenerated or replaced by current local summaries when a saved packet is read.
The supporting details retain method, inputs, bounds, exclusions and saved
materials. Screen and print use the same source snapshot. No-match responses
are labeled search results, not AI interpretations or evidence of novelty.

Worker version `4fe938f2-437b-44bc-82de-b078b832a6ef` uses cache version
`research-v15-source-findings` and asks for a short explanation of overlap and
differences without repeating the authored findings. One live check on
24 October 2026 recognized the executed LP2-15 row reversal and correctly left
readable English unestablished. It still described the target set too broadly
as all LP2 pages and paraphrased the inconclusive score comparison as a
non-significant difference without a declared threshold. The answer is therefore
not a fully accepted scientific comparison. Prompt guidance, citations and exact
source binding do not validate every inference. Further work must preserve the
difference between matching known openings, scoring outputs and demonstrating
readable text; a generic outcome label cannot substitute for that distinction.

## Direct comparisons from reviewed execution records

`recorded-comparison.js` handles exact supported operations before model selection.
It currently supports one confirmed row-rune reversal on explicit whole pages,
with no extra steps, parameters, unresolved constraints or specified rules.
Its authority comes from validated `recorded_comparison` execution metadata,
never discovery tags or a record title. Each retained source must cover every
requested page. Other requests continue through the ordinary comparison path.
Execution metadata travels separately as `recordedComparison` in direct source
documents. It does not enlarge or change the model's evidence text or retrieval
budget. Direct responses bind both this metadata and the ordinary source text.

The row-route record contains 55 executed pages; its English-scoring companion
contains 53 eligible pages. LP2-50 has no row-route input; LP2-49 and LP2-55 do
not meet the scorer's 100-quadgram minimum. The evidence checker verifies saved
permutations, output indices, source positions, score eligibility and hashes
without rerunning the searches. These records establish the executed operation,
not equivalence with unspecified settings or success at the visitor's objective.

Direct replies use no AI binding or answer cache. They retain normal request
validation, rate limits, source loading and confirmed-card binding. The browser
recomputes the reply from the same normalized transport card and exact cited
evidence before accepting its type. Screen and printed packets show the authored
findings first, with no AI-attribution label on a validated direct comparison.
The comparison describes the matched operation, input treatment and evaluation;
it does not repeat the already-visible findings and limits. Complete metadata
and saved-output descriptions remain in the cited sources.
The broader source-guidance prompt remains version 15; this is not an improvement
claim about untested model responses.

Checks: `node scripts/test_recorded_comparison.cjs`,
`node services/idea-assistant/test-recorded-comparison.mjs`,
`node scripts/test_investigate_recorded.cjs`, and
`python scripts/check_recorded_row_routes.py --self-test`.


## Reviewed-plan admission

Migration `0008_prepared_plans.sql` must be applied before deploying the Worker
and the receipt-dependent run page. Preparation creates an internal immutable
authorization, not a public experiment or result. It binds the original canonical
idea, complete task, input version, parent and known-answer controls. Validated
wording mappings and remaining-page extensions retain their server-side basis.

Generic task creation requires `preparationId`, or an exact previously issued
binding for older clients. It never recompiles or reinterprets an idea at creation.
Changed or unissued plans receive 409 and must be prepared again. Existing exact
idea associations remain retryable, and reviewed record origins keep their
separate verified admission path. Applying the additive migration before the
Worker supports the previous frontend without admitting arbitrary tasks.

Checks: `node services/idea-assistant/test-prepared-plans.mjs` from the repository
root, alongside the preparation, task, extension and browser UI suites.


`POST /tasks/:id/variants` prepares the fixed word-boundary comparison for an
eligible saved measurement. Migration `0009_word_boundary_preparations.sql`
extends the receipt authority set while preserving earlier authorizations.
Apply it before deploying the variant-dependent Worker and frontend. The shared
`experiment-protocols.js` definitions supply the measurement constraints and
presentation; the numerical engine and independent controls remain separate.

## Full finite searches

`/factored-search/:proposalId/{evidence,prepare,create,results}` preserves the
complete confirmed question while preparing at most twelve ordinary cases at
a time. The browser checks one paged evidence snapshot, then asks for fresh
evidence only for its next selected cases. Original result receipts remain
the evidence; local progress and stored checkpoints are not public results.

Apply `0013_finite_evidence_epoch.sql` and install the dedicated Worker secret
`FACTORED_EVIDENCE_CURSOR_KEY` before deploying this route. Configure the
frontend's `factoredSearchEndpoint` only after that deployment. The original
finite route and its admission limits remain available for existing clients.
The results route accepts previously admitted immutable tasks even if current
source text changes; preparation requires a fresh matching snapshot.

The browser uses IndexedDB for bounded original receipts and pending output.
Storage failure stops the full search visibly rather than dropping cases.
Large offline audits are downloaded as bounded ZIP parts; every advertised
part is required for the independent Python check. No missing cases run during
export or audit.

Checks: `scripts/test_factored_search_http.mjs` (Node SQLite),
`scripts/test_factored_search_session_adversarial.cjs`,
`scripts/test_factored_finite_workspace.cjs`, and
`scripts/test_factored_finite_workspace_adversarial.cjs`.

## Shared finite source storage (0014)

Apply migration 0014 before deploying the source-aware finite Worker. It adds
immutable shared snapshots and lightweight task-origin references, retaining all
old origin bytes and the existing response shape. Local SQLite and private
browser QA cover migration compatibility, quotas, tampering, source changes and
save/reload. The October 25 deployment attempt was stopped before migration by
Cloudflare account authorization error 7403; these changes are not claimed live.
