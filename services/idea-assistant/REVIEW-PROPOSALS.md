# Manual proposal review

The **original confirmed standardized idea is the intake**. Users should not re-enter it in a separate proposal or “Suggest a test” form. The live intake stores confirmed cards and original wording in the private D1 review queue. The offline reconciliation command below prepares saved cards for owner comparison with published research. It does not determine genuinely new parts automatically.

The current schema preserves an exact standardized card and associated submission notes/source links. Exact-card identity is not semantic novelty: differently worded cards may overlap, and an unchanged method can have untested scope. The tool does not automatically identify new parts, infer coverage, create an experiment, run code, call a model, add a method category, or publish a finding. Acceptance records a maintainer decision for further consideration or planning, not proof that the proposal is new. A later reproducible experiment still needs its own fixed inputs, protocol, controls, outputs and publication review.

`review-proposals.mjs` is a small maintainer CLI. There is no public administration page. It uses an already installed Wrangler JavaScript entry through `process.execPath`, with an argument vector and `shell:false`. It does not install packages, log in, request broader permissions, deploy, follow submitted URLs, or call AI.

Queries use Wrangler's `--command` argument. Remote `--file` invokes bulk import
and does not return the rows required by this review tool. SQL is passed as one
literal argument, never interpolated into shell code.

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

## Prepare private owner comparison offline

The pending cards already hold incoming ideas. Reconciliation makes that saved material reviewable alongside existing research; it does not create a second intake form or decide which parts are new.

```text
node services/idea-assistant/reconcile-ideas.mjs --input ../qa-temp/review-pending.json --out ../qa-temp/owner-review-NEW
```

`--input` is an explicit `review-proposals.mjs export` file. `--out` is a **new directory outside this public repository**, with an existing parent directory. Existing outputs and repository-contained paths, including paths redirected through a symlink/junction, are refused. The output consists of `queue-review.json` and `queue-review.md`. Keep both private. Optional `--registry FILE` selects another saved published registry; the default is local `data/experiments.json`. There is no database access, model call, URL fetch or package installation.

Use a complete selected-card export: `notes_complete_for_selection` must be true, `next_after_note` must be empty, and every card's `submission_count` must match its preserved contribution rows. For large ledgers, request fewer cards or export one card with enough note capacity; a partial note page cannot be reconciled silently. A card cursor (`next_after`) is allowed and prominently retained: the report covers that selected page, not the entire queue. Export reads may span concurrent changes; they are not a transactional database snapshot.

Validation requires the export schema, read timestamps, matching/selected counts, and complete `cards`/`submissions` arrays. Each card needs its full `id`, `card_hash`, canonical `card_json`, parsed `card`, matching share `fragment`, valid review status and `submission_count`. Every contribution needs its unique UUID `request_id`, selected `proposal_id`, `original_idea` (empty is allowed), `note`, `source_url`, UTC `received_at` and matching `received_day`. Original wording is required even when empty, so an older export cannot silently lose it. Hash/ID disagreement, noncanonical or mismatched active cards/fragments, orphan or repeated contributions, missing notes and stale linked published-record IDs fail before any output directory is created.

The report retains original wording and every contribution/source separately from the exact standardized card. Exact card identity groups contributions without turning multiple notes into additional ideas or results. `compareCards` enumerates relationships between incoming cards, including directional page additions/removals; parameter, ordered-operation, rule-state and qualified-passage differences remain explicit. It does not equate broad and narrow scopes or infer semantic novelty.

Published candidates come from the existing `AssistantSearch.select` method gates and bounded selection. Ranking uses the standardized ordered method, parameters and rule terms; original wording, outcome text and scope prose do not rank records. Pages are passed separately for overlap tie-breaking. An unspecified/ambiguous method requires clarification, an overlong method query requires shortening, and no selected candidate means **needs comparison**, never “new”. Compound methods still require human comparison of every operation and limit. The report includes each candidate's entire published registry record, citation, scope/exclusions, findings and limitations, without converting related results into exact coverage. Input/registry byte hashes and local code hashes identify the snapshot.

The readable report places supplied wording, notes, URLs, cards and registry prose in escaped inert text blocks; it creates no remote embeds. Only validated experiment IDs on the fixed published wiki origin become clickable citations, usable from a local report. Counts distinguish saved incoming cards and contributions from maintainer review status; newly created tasks and executed experiments are always zero. An owner can then make an explicit review decision and, when warranted, plan a separate reproducible experiment with fixed inputs and controls.

Inputs are limited to 8 MiB, 100 cards and 1,000 contributions; the registry is limited to 64 MiB and the combined report to 32 MiB. Oversized output fails rather than dropping scopes, contributions or relationship differences.

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
node services/idea-assistant/test-reconcile-ideas.mjs
```

Tests use actual `node:sqlite` in-memory tables with all three migrations and injected CLI I/O. They cover explicit modes/IDs, bounds and cursors, exact cards/original wording, distinct counts, later notes, full review transitions, SQL quoting of adversarial reasons, safe process arguments, real published-record links, stale-status conflicts and immutable card/submission bytes. They do not execute Wrangler, access a remote database or call a model.

Reconciliation tests use valid active-card fixtures and the actual saved published registry. Temporary input/report files stay outside the repository and are removed after verification. They cover complete contribution preservation, method-only ranking, page deltas, complete candidate evidence, integrity failures, private output boundaries, escaping and byte snapshots. They do not write synthetic review output into public data.
