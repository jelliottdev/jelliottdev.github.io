# Confirmed idea intake backend

`services/idea-assistant/proposals.mjs` is a separate persistence handler. It
does not call AI, run an experiment, fetch source URLs, authenticate a person,
or publish a proposal. The deployed Worker routes `/proposals` to
`handleProposal(request, env)` with the D1 and rate-limit bindings provisioned.
Implementation tests use local fixtures without remote database operations.

## Request and response

POST saves the original confirmed idea from exactly `env.SITE_ORIGIN` as part of
the explicit confirmation/check action. It is not a separate proposal form or
a client-side novelty decision. Internal reconciliation decides how to review
and queue the idea. The route is enabled in production; loading or importing a
page alone does not save an idea.

```json
{
  "requestId": "b5a70826-d086-44f6-b20a-85e756d632d3",
  "fragment": "#idea=<versioned bounded ClaimShare payload>",
  "originalIdea": "Original human source idea, at most 8000 characters",
  "note": "Optional supporting detail, at most 1200 characters",
  "sourceUrl": "https://github.com/example/project/blob/main/method.py"
}
```

`requestId` is a standard-variant UUID with version 1–8, normalized to lowercase.
The body is JSON, at most 32,000 bytes, with no extra fields. Optional note and
source fields must be strings when present; null is rejected. `originalIdea` is
optional exact original human wording, at most 8000 characters, retained with its
submission separately from card identity. The frontend must omit synthetic
shared-link summaries rather than label them original human wording. It must
not send AI answers, conversation transcript, attachment content or edit history.
The combined request must still fit 32,000 bytes. `sourceUrl` is at
most 1500 characters and must be HTTP(S), without credentials or an obvious
local/private host. URLs are only stored, never fetched or DNS-resolved. Host
syntax checks do not certify the accessibility or trustworthiness of a source.

The server decodes through `ClaimShare`, requires a specified nonempty method,
and confirms/re-encodes the validated standardized draft internally to produce
a canonical active card. That internal confirmation validates the card's
structure; it is not a claim that a new experiment was executed. Scope and rule
unknowns remain explicit. Original wording remains absent from the share payload
and canonical card; the intentionally supplied `originalIdea` field is stored
separately. Results, attachments, source provenance and edit history are not
stored. Active step wording/parameters and standardized fields remain the card.

Successful response (HTTP 200):

```json
{
  "id": "p_<64 lowercase SHA-256 hex characters>",
  "status": "received",
  "receivedAt": "2026-10-24T12:00:00.000Z"
}
```

An allowed exact retry returns `already_received` with its original timestamp.
Reusing a requestId with changed card/originalIdea/note/source returns 409. The frontend must
retain requestId across retries and rotate it when any submitted content changes.
Responses expose no pending queue or review details. Errors are generic JSON
`{error:string}`: malformed input 400, wrong/missing Origin 403, wrong path 404,
unsupported method 405, conflicting idempotency 409, limits 429, and unavailable
configuration/rate/database 503. Internal SQL/errors are not returned.

## Bindings, CORS and limits

- `SITE_ORIGIN`: exact HTTP(S) origin, with no trailing path/slash.
- `PROPOSALS`: D1 database with the migration applied.
- `PROPOSAL_LIMIT`: rate-limit binding supporting `limit({key})`.

POST and OPTIONS are supported. Preflight permits only POST and Content-Type;
successful authorized responses set exact-origin CORS, `Vary: Origin`, and
`Cache-Control: no-store`. Missing bindings fail closed. CF-Connecting-IP is
used transiently as the rate-limit key (missing header shares the `unknown`
bucket); it is never persisted or included in hashes. Rate limiting runs before
every D1 read, including retries. A retry may therefore be temporarily throttled.

The database enforces an overall cap of 50 new submissions per UTC day using two
conditional INSERTs inside one D1 `batch` transaction. Both check the durable
submission count; card creation also checks requestId existence. No concurrent
transaction can interleave between these statements. Unique request IDs prevent
double insertion. After an allowed retry, existing submission lookup returns
before the daily cap, so retries never count twice even when the daily cap is
full. Failure rolls back both statements; no card is created without its first
submission. This cap is not merely an in-memory counter or an edge rate limit.

## Stored identity and reviewing

Migrations: `services/idea-assistant/migrations/0001_proposals.sql`,
`0002_proposal_reviews.sql` and `0003_original_idea.sql`, applied in order.

`proposals` contains `id`, unique `card_hash`, canonical `card_json`, canonical
`fragment`, `created_at`, and administrative `status`, `reviewed_at`,
`review_reason`, `record_id`. Status is pending/accepted/duplicate/declined.
`proposal_submissions` contains immutable `request_id`, `proposal_id`,
`request_hash`, `note`, `source_url`, `received_at`, `received_day`,
`original_idea` (NOT NULL, default empty string, maximum 8000 characters).

Card identity is SHA-256 of deterministic key-sorted active-card JSON. Object
member order is immaterial; ordered steps, exact wording, all parameters, scope
holes, and explicit states remain distinct. Original wording/note/source are excluded from card
identity, but every new requestId contributes a separate immutable submission.
Exact duplicate cards therefore retain additional notes/sources rather than
discarding them. These are structural duplicates only; there is no automatic
semantic equivalence/novelty judgment or user-created category. Existing family
IDs are descriptive card metadata, not coverage evidence.

Maintainers review stored cards and contributions separately. A later note on a
previously reviewed card is preserved without silently changing its review
status; review tools should show recent submissions as well as pending cards.
Administrative decisions should use an expected-status conditional update and
check one changed row, preserving the card and notes. No public pending-list
endpoint is exposed here.

`proposal_reviews` records each actual change to status, reviewed_at,
review_reason or record_id through an AFTER UPDATE trigger. Each row contains an
autoincrement id, proposal_id, changed_at (database UTC timestamp), and old/new
values for all four fields. NULL-safe comparisons prevent no-op updates from
fabricating decisions. A correction such as accepted→declined appends the prior
reason and linked record rather than losing them. The trigger does not alter
active cards or contribution notes. History orders by id within a card and does
not imply an independently authenticated reviewer identity.

## Local verification

```text
node services/idea-assistant/test-proposals.mjs
```

The test uses Node 24 `node:sqlite` with a real in-memory database and transaction
adapter for D1's prepare/bind/first/batch interface. It applies the exact SQL
migration, checks explicit Origin/bindings/body/source guards, canonical identity,
notes, exact optional original wording and its bounds/idempotency, rate-before-read,
rollback, idempotency and old/new review audit history.
No-op updates append no audit rows, including unchanged NULL fields. Seventy-five concurrent
requests produce exactly fifty rows; eight same-ID concurrent retries produce
one row; an allowed retry at the daily cap retains the original timestamp; a
new UTC day admits a new submission. SQL is executed locally, with no remote
database, credentials, deployment, AI, or network requests.
