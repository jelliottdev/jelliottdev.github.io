# Manual proposal review

The **original confirmed standardized idea is the intake**. Users should not re-enter it in a separate proposal or “Suggest a test” form. This document covers reusable internal storage/review scaffolding only; live intake activation is paused. Automatically saving that original card and reconciling its genuinely new parts into a work queue is a separate integration step, not something this CLI implements or certifies.

The current schema preserves an exact standardized card and associated submission notes/source links. Exact-card identity is not semantic novelty: differently worded cards may overlap, and an unchanged method can have untested scope. The tool does not automatically identify new parts, infer coverage, create an experiment, run code, call a model, add a method category, or publish a finding. Acceptance records a maintainer decision for further consideration or planning, not proof that the proposal is new. A later reproducible experiment still needs its own fixed inputs, protocol, controls, outputs and publication review.

`review-proposals.mjs` is a small maintainer CLI. There is no public administration page. It uses an already installed Wrangler JavaScript entry through `process.execPath`, with an argument vector and `shell:false`. It does not install packages, log in, request broader permissions, deploy, follow submitted URLs, or call AI.

## Setup and explicit database mode

Apply `migrations/0001_proposals.sql`, `0002_proposal_reviews.sql` and `0003_original_idea.sql` to the selected database. The first stores immutable cards/submissions; the second appends old/new metadata to `proposal_reviews` when a review changes; the third preserves original idea wording separately from standardized-card identity. Root owns database setup and deployment.

Configure the installed CLI path, for example in PowerShell:

```powershell
$env:LIBERPEDIA_WRANGLER = 'C:/absolute/path/to/node_modules/wrangler/bin/wrangler.js'
```

Alternatively pass `--wrangler` with the same absolute `.js` path. There is no `npx` or network-install fallback. Execution requires explicit `--local` or `--remote`; omitting both fails before a database command. `--dry-run` prints the first SQL operation without contacting a database.

`--local` defaults to database `liberpedia-proposals-local`, config `services/idea-assistant/wrangler.proposals-local.jsonc`, and Wrangler's default local state in the service directory. `--persist-to DIR` can select another local store. `--remote` defaults to `liberpedia-proposals` and the production `wrangler.jsonc`; it requires already authorized D1 access. `--database NAME` and `--config FILE` explicitly override those defaults. This tool never grants D1 permission itself.

## Read the queue and exact card

From the repository root:

```text
node services/idea-assistant/review-proposals.mjs list --local --limit 20
node services/idea-assistant/review-proposals.mjs list --local --new-notes
node services/idea-assistant/review-proposals.mjs list --local --status accepted
node services/idea-assistant/review-proposals.mjs show --local --id p_FULL_64_HEX_HASH
```

Replace the placeholder with the entire `p_` plus 64 lowercase hex ID copied from the list. `list` defaults to pending cards. `--status pending|accepted|duplicate|declined|all` selects other review states. `show` reads one exact ID regardless of state, including its submission notes and review history. Exact JSON, parsed readable JSON, original share fragment, card hash, timestamps and review metadata are retained. The CLI verifies that `SHA256(card_json)` agrees with both `card_hash` and the proposal ID; it does not reword or normalize the submitted card.

Counts distinguish **distinct cards** from **submissions**. Two notes for the same exact card are two submissions and one card, never two experiments. The backend has already fixed card identity; similarity, broad categories and a maintainer's judgement do not merge cards in this tool.

A new note on an accepted/declined/duplicate card does not reset its review status or erase its old decision. `--new-notes` defaults to all statuses and selects reviewed cards with submissions received after `reviewed_at`. Each listed card also reports `unreviewed_submission_count`. Read these contributions explicitly; do not rely only on the pending view.

## Bounded offline export

```text
node services/idea-assistant/review-proposals.mjs export --local --out review-pending.json --limit 20 --note-limit 200
node services/idea-assistant/review-proposals.mjs export --local --status all --id p_FULL_64_HEX_HASH --out review-one-card.json
```

Exports refuse to overwrite an existing file. They contain exact immutable cards, original idea wording and associated submission notes/source URLs, the selected filter and read timestamps. Original wording is separate from the standardized card and is not an AI transcript or edit history. Keep exports private to the review workflow; they may contain supplied material and should not be committed or published automatically.

Limits are 100 cards, 1,000 submission notes and 8 MiB of serialized output. An oversized output fails rather than truncating a card or note. `next_after` is a card-ID cursor. `next_after_note` is a submission UUID cursor; continue with `--after-note UUID`. Notes are ordered by UUID, not arrival time. For a large single-card ledger, use `--status all --id ID` while paging its notes. `notes_complete_for_selection` makes a partial export explicit.

`show` includes the latest 100 review transitions by default. Use `--history-limit N` and `--before-review N` with its `next_before_review` cursor for earlier history. Metadata, notes and history are separate bounded reads, not a transactional snapshot of an actively changing queue.

## Record one explicit review decision

First inspect the exact card, all relevant notes and existing evidence. Then use an explicit ID, decision, expected current status and reason:

```text
node services/idea-assistant/review-proposals.mjs decide --local --id p_FULL_64_HEX_HASH --status accepted --expected-status pending --reason "Accept for a bounded protocol; no experiment has run."
node services/idea-assistant/review-proposals.mjs decide --local --id p_FULL_64_HEX_HASH --status duplicate --expected-status pending --reason "The supplied operation matches this existing bounded record; its exclusions still apply." --record lp2-fibonacci-openings
```

Decisions are `accepted`, `duplicate` or `declined`. Unknown statuses are rejected. Optional `--record` must identify an actually **published** record in the local `data/experiments.json`; it does not publish a draft or certify exact coverage. Without `--record`, an existing related-record link is preserved.

The update targets only `status`, `reviewed_at`, `review_reason` and optionally `record_id`, with `WHERE id=… AND status=expected`. It returns the changed row atomically. A missing card or changed status is a conflict, not success; refresh before trying again. There is no silent retry with another expected status. Correcting an accepted decision is explicit (`--expected-status accepted`), and migration 0002 retains the complete old/new metadata transition. Exact no-op metadata updates do not add a history row. Cards, fragments, notes, source links and request IDs are never updated by review commands.

Use `--remote` only when deliberately reviewing the production queue with authorized credentials. The examples above remain local. No production review command was run during tooling validation.

## Local tests

```text
node services/idea-assistant/test-review-proposals.mjs
node services/idea-assistant/test-proposals.mjs
```

Tests use actual `node:sqlite` in-memory tables with all three migrations and injected CLI I/O. They cover explicit modes/IDs, bounds and cursors, exact cards/original wording, distinct counts, later notes, full review transitions, SQL quoting of adversarial reasons, safe process arguments, real published-record links, stale-status conflicts and immutable card/submission bytes. They do not execute Wrangler, access a remote database or call a model.
