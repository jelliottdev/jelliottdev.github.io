# Hosted idea comparison

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
stays undecided; original wording remains visible for review. Saving and queue
intake remain unconfigured (`proposalEndpoint: null`).

One uncached interpretation makes one generation, with no automatic repair or
retry. A 20-second response deadline, three active provider slots per isolate,
the existing rate-limit binding, exact-input cache and singleflight bound work.
A timed-out generation retains its slot until the provider settles. These are
not a global daily quota. See `docs/frontend/claim-specification.md` for the
review contract and `test-interpret-handler.mjs` for offline verification.

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

The Worker retrieves the public experiment registry and a compact supporting-page index, cached for five minutes. It ranks **techniques first**, after removing page references from the query. A page match alone never triggers inference. At most two complete experiment scopes and two relevant excerpts from explicitly named pages are sent to the model. Page evidence is supporting context, not evidence of a test. Retrieval is lexical, not an exhaustive semantic or novelty check.

Concurrent cold requests share one index load. A failed or malformed optional supporting-page index leaves the experiment records usable; a failed experiment registry still stops comparison rather than substituting page context for evidence. The next load after the five-minute expiry picks up published record changes. Loader tests simulate refreshes, failures and recovery without network access.

Only published experiment records are eligible. Empty registries, page-only requests and unmatched techniques do not spend inference. Experiment scope is never silently truncated to fit a prompt. The strongest match must fit the 9,000-character experiment allowance; a second match is included only if both fit. If the second cannot fit, the first remains usable and the ordinary result list still exposes the other records. An oversized strongest match stops inference rather than substituting a weaker match. Total context is bounded to 11,000 characters and output to 700 tokens (requested prose limit: 220 words). Thinking is disabled. Citations are checked for valid source numbers, which does not prove factual entailment. Markdown rendering escapes HTML and only links to evidence-owned wiki routes.

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
