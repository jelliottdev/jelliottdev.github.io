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

The Worker retrieves only the public Liberpedia registry, cached for five minutes. It ranks records with the same lexical retrieval as the site, passes up to three complete scopes/findings/limitations to the model, and rejects missing or out-of-range citation numbers. Citation validation does not prove factual entailment. Real answer-quality review is needed once records exist.

Only published records are eligible. Empty or unmatched requests do not spend inference. Input and output are bounded; large record contexts fall back to the full records rather than silently truncating scope. The browser times out and falls back to ordinary results when needed.

The configured rate limit permits six requests per minute per IP at a Cloudflare location. This is not a global quota or a guarantee against abuse; Origin checks are also not authentication. Workers Free provides the cost ceiling. Anonymous public access can exhaust the free allowance, in which case the site keeps serving search results. No automatic paid fallback is configured.

Queries and retrieved text are sent to Cloudflare for processing. The Worker does not store queries or log request bodies; observability is disabled. Cloudflare's service policies still apply. A short disclosure appears below the form when the hosted endpoint is configured.

## Validation

Run `node services/idea-assistant/test-worker.mjs` from the repository root. Tests use a fake inference binding and never consume hosted quota. Complete a real deployed integration check before enabling the endpoint. Do not call the hosted assistant operational while `endpoint` is null.

Official documentation checked 19 October 2026:

- [AI bindings: no secret keys required](https://developers.cloudflare.com/workers-ai/configuration/bindings/)
- [Free allowance and hard limit](https://developers.cloudflare.com/workers-ai/platform/pricing/)
- [Rate-limit binding](https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/)

Puter requires visitor sign-in and uses visitor allowances/billing. Pollinations generation now requires keys. Neither meets the requested friction-free visitor experience as directly as a hosted binding on the free plan.
