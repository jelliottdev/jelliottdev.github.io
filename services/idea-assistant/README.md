# Hosted idea comparison

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

Only published experiment records are eligible. Empty registries, page-only requests and unmatched techniques do not spend inference. Experiment scope is never silently truncated to fit a prompt. Context is bounded to 11,000 characters and output to 700 tokens (requested prose limit: 220 words). Thinking is disabled. Citations are checked for valid source numbers, which does not prove factual entailment. Markdown rendering escapes HTML and only links to evidence-owned wiki routes.

Repeated requests reuse answers in three ways: a bounded browser-memory cache (20 entries, one hour), bounded Worker memory (100 entries, one hour), and the Cloudflare Cache API (up to 24 hours). Cache keys hash the exact whitespace-normalized question, selected pages, evidence contents, model and prompt version; case is preserved for cryptographic questions. Changed evidence invalidates an answer. Edge cache entries are local to a Cloudflare data center and may be evicted; this is not a global or guaranteed hit rate. Equal concurrent requests share one inference within an isolate. Three concurrent generations per isolate and a 60-second outage cooldown reduce retry storms; these are not account-wide limits.

The browser only requests inference on explicit submission when related experiments exist. It does not call the model on keystrokes, route opening, page selection, or ordinary wiki navigation. Repeat submission is disabled while waiting. Stopping the wait cancels the browser request but cannot promise to cancel already-started inference or refund quota.

The configured rate limit permits six requests per minute per IP at a Cloudflare location. This is not a global quota or a guarantee against abuse; Origin checks are also not authentication. Workers Free provides the cost ceiling. Anonymous public access can exhaust the free allowance, in which case source records remain usable. No automatic paid fallback is configured.

Questions and retrieved text are sent to Cloudflare. The Worker does not log request bodies; observability is disabled. Answers and their source excerpts are temporarily cached and can be reused for the same question. The cache URL contains a SHA-256 digest, not the question; generated answer text can nevertheless reflect the submitted question. The form advises users not to include private information, and the coverage disclosure explains reuse. Cloudflare's service policies still apply.

## Validation

20 October 2026: deployed optional-context failure handling and shared index loads as Worker version `4cb2c95a-8273-4480-a1ae-46eaffdfcde2`. Mocked tests cover current published records, complete evidence preservation, five-minute refresh, load failures and retries. Wrangler confirmed deployment with the existing AI and rate-limit bindings. No hosted inference request was made for this deployment; it is not a new model-quality evaluation.

Run `node services/idea-assistant/test-worker.mjs` and `node scripts/test_assistant.cjs` from the repository root. Tests use a fake inference binding and never consume hosted quota. Complete a real deployed integration check before enabling the endpoint. Do not call the hosted assistant operational while `endpoint` is null.

One remote synthetic-fixture smoke test on 19 October 2026 used one model generation: approximately 3.3 seconds cold and 0.7 seconds for a cached repeat. The answer correctly distinguished one synthetic row from all manuscript rows. This is not a latency benchmark or an evaluation on real experiment records. The public registry remained empty.

Official documentation checked 19 October 2026:

- [AI bindings: no secret keys required](https://developers.cloudflare.com/workers-ai/configuration/bindings/)
- [Free allowance and hard limit](https://developers.cloudflare.com/workers-ai/platform/pricing/)
- [Cache API and data-center locality](https://developers.cloudflare.com/workers/runtime-apis/cache/)
- [Rate-limit binding](https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/)

Puter requires visitor sign-in and uses visitor allowances/billing. Pollinations generation now requires keys. Neither meets the requested friction-free visitor experience as directly as a hosted binding on the free plan.
