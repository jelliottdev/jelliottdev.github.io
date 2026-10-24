# Claim model integration contract

Core model: `claim-specification.js` and `scripts/test_claim_specification.cjs`.
The standalone surface and Worker context contract are described below. The handoff's curated
research results and example identifiers such as `method=covered` are not imported.

## Loading and principal shapes

Classic browser script exposes `globalThis.ClaimSpecification`. Node/Worker's
existing CommonJS interop pattern can use `require()` / default import like
`assistant-search.js`. No DOM, network, storage, model call or experiment runner.

```js
const C = ClaimSpecification;
const supplied = {kind:'supplied', refs:['source:text']};
const known = value => C.field('specified', value, supplied);
let draft = C.createDraft({
  source: {text: originalExactText, materials: [{name:'proposal.png'}]},
  // Aim stays unspecified unless actually supplied or explicitly proposed.
  method: known({operations:[{id:'reverse_row_runes'}]}),
  scope: known({pages:['lp2-15','lp2-17']}),
  rules: {wordBoundaries:known('preserve')}
});
const question = C.questions(draft)[0]; // id, prompt, example, choices[]
draft = C.clarify(draft, question.id, 'within_words');
const rows = C.reviewRows(draft); // label + tags[{id,text,unknown}], details?
const snapshot = C.confirm(draft, {id: uniqueClientId, at: new Date().toISOString()});
const request = C.queryForResearch(snapshot, {maxLength:1500});
```

`source.text` retains whitespace and code exactly. Materials default to
`contentStatus:'metadata_only'`; metadata does not mean bytes were read or OCR
performed. Add extraction provenance explicitly if extraction becomes real.
Every interpreted field has `status`, optional `value`, and provenance
`{kind,refs}`. States: `specified`, `unspecified`, `not_applicable`,
`unrestricted`. These never stand in for one another. Origins: `supplied`,
`user_clarification`, `project_context`, `proposed`. No default GP table or aim.

Method is an ordered operation list; operation IDs are semantic names, never
coverage verdicts. Recognized display IDs are `reverse_row_runes` and
`reverse_value_digits`; other operations and their JSON parameters are retained.
Rules are representation, wordBoundaries, boundaryMode, unmapped, inputVersion,
evaluation, reset, initialState, searchBounds, searchProtocol, exceptionalCases.
Unknown method-specific details belong in operation parameters or `unresolved`,
not silently discarded fields. Nested `{status:'unspecified'}` parameters appear
in the completeness report. Method order is never sorted.

Scope is a stateful object whose `pages` are exact page IDs. Sorting/deduplication
is harmless; filling holes is forbidden. An explicit empty page set remains
empty, while unknown scope remains unknown. Other scope properties such as a
position selection or artifact identity are retained. Page membership alone
does not imply a whole-page run or continuous state equivalence.

## Stable outcome and method vocabulary

`OUTCOMES` is the frozen registry: `decipher` (Decipher the text), `measure`
(Test a pattern), `reproduce` (Reproduce a result), `explain` (Explain a feature),
and `verify_source` (Verify source material). `normalizeOutcome(value)` returns
`{id,label,wording,detail}`. Exact aliases such as “solve LP2”, “decipher LP2”
and “find readable text” share `decipher`; their exact wording remains distinct.
The category states an intended outcome, not a full-solve acceptance criterion.
Negative, quoted, compound and otherwise unmatched wording is `unclassified`;
visitors cannot create new registry categories.

Existing string `aim.value` remains supported. Controlled selection can supply
`{outcomeId,wording,detail}`. A valid selected category is authoritative even when
details change. For `unclassified`, the current detail is checked for an exact
alias before falling back to wording when detail is absent. This prevents both
duplicate aliases and stale original wording overriding a custom edit.
`normalizeAim(field)` preserves the exact value and recomputes derived `outcome`;
create/revise use it, and `validateConfirmed` rejects inconsistent derived data.
`outcomeLabel(fieldOrId)` supplies the stable display label. Category equality
does not imply exact meaning, scope, protocol or coverage equality.

`METHOD_FAMILIES` (also `METHODS`) contains existing research family IDs:
`fixed-substitution`, `polyalphabetic`, `feedback`, `transposition`,
`prime-indices`, `number-streams`, `book-codes`. Explicit broad selection is
`{id:'family_selection',familyId,label}`. It does not supply execution rules.
`classifyMethod(methodField)` returns `familyIds`, `complete`, and ordered
`operations` rows containing index, familyId, label, basis and the exact copied
operation. Classification recognizes inspected operation IDs and anchored small
names; negative/code/compound wording is left unclassified. No operation,
parameter or original wording is rewritten. Families are browsing vocabulary,
not evidence of equivalent methods or a coverage verdict.

Both query helpers return a null query with `needsClarification:true` when a
meaningful method is absent. Compact retrieval puts method/scope/rules first,
omits generic outcome labels, and retains unmatched specific aim wording. Full
confirmed context still includes all exact intent, source and protocol fields.

### Ordered method editing

`applyMethodEdit(draft, edit)` returns a fresh revised draft. Supported edits:
`{type:'add',index,operation}`, `{type:'remove',index}`,
`{type:'move',index,toIndex}`, `{type:'wording',index,text}`,
`{type:'replace',index,operation}`, and `{type:'category',index,familyId}`.
Indices refer to the current ordered list; move destinations refer to its final
position. Add accepts the end index. Removing the last step makes the method
unspecified, so automatic research is blocked. Source text is never modified.

Untouched steps retain their exact JSON, including parameters and provenance.
Wording edits deliberately create an opaque `described_method`, retaining exact
new wording and original source correspondence but retiring the previous ID and
parameters. Structured replacement requires the caller's deliberate full new
operation. `draft.methodEdits` retains previous complete operations, removed
constraints and index mappings separately from active method semantics. History
is part of snapshot binding, but does not supply active keys or readiness rules.

Indexed constraints follow their original step through moves/additions. Removing
or replacing its step retires those constraints into history; independent
constraints remain active. A formerly implicit single-step ambiguity gets an
explicit index before a sibling is added. Explicit reversal boundary handling is
retained when an independent cipher is appended or unchanged steps are moved;
changing/removing the reversal itself requires a new boundary answer.

Category edits store a separate `declaredFamilyId` annotation (`null` clears it)
without replacing exact operations or parameters. Classification reports a
conflicting declaration as `category_conflict`, never silently redefines the
operation. Opaque safe wording can receive a declared family without acquiring
execution rules. Editors should use local draft copies until Review changes;
Cancel restores the original confirmed/result snapshot. Scope/rule editors
should similarly patch only changed fields rather than reconstructing defaults.

## Interpretation and clarification boundary

`fromText(text,materials)` only creates an uninterpreted draft. It is deliberately
not the handoff's fixture-matching parser and not a general code/NLP interpreter.
Production must provide supported, inspected structured interpretation through
`createDraft` or `revise`, or add a separately validated normalization stage. Do
not display invented tags just because arbitrary text was accepted. Unknown
scope/aim need not block research after a meaningful method is represented.

For ambiguous reversal, append a source-referenced constraint
`{kind:'operation_ambiguity',text:'...',operationIndex:0}`. `questions()` returns
the two concrete meanings and Other. Compound methods must identify the affected
operation; clarification preserves other operations and their parameters.

For row-rune reversal plus `wordBoundaries='preserve'`, `questions()` asks the
three distinct meanings with AB CDE examples: BA EDC, ED CBA, CDE AB. Their
`boundaryMode` values are `within_words`, `fixed_spaces`, `word_blocks`.
Clarifying scope retains the chosen boundary mode. Changing method clears that
mode for revalidation; switching back asks again. Independent rules and unknown
constraints survive. Other text is saved without pretending it was interpreted;
it remains unsupported for automatic comparison until an explicit interpretation
is provided. No fixed number of choices is imposed on unrelated ambiguities.

`reviewRows` is compact Aim/Method/Scope/Rules, not a full protocol form. It shows
specified/unrestricted rules and the consequential unknown unmapped-value rule
for digit reversal. `completeness()` exposes secondary execution gaps separately.
Its readiness flags concern declared fields, not proof that arbitrary code is
executable or that a protocol is scientifically adequate.

## Confirmation, research, packet and cache

`revise(draft,typedPatch)` copies, increments revision and clears confirmation.
It never mutates the original or changes source material. A source edit should
create a new draft from the new source, retaining the old snapshot externally.
There is no automatic relabeling of old results. `confirm(draft,{id,at})` blocks
unresolved consequential choice questions, but can confirm an accurately
represented incomplete idea. It deeply freezes the snapshot, records canonical
summary, and sets `execution:'not_run'` regardless of completeness. This is
interpretation approval, not execution or authenticated human-signature proof.

`validateConfirmed` checks a deserialized snapshot. `binding(snapshot)` is
deterministic canonical JSON, **not** a cryptographic signature or experiment
identity. Hash this string for a compact server/cache key if needed.

`queryForResearch` includes the ordered method, exact scope, all rule states,
and separately labeled original wording/material metadata. It returns
`{query,pages,needsShorter,needsClarification,length,maxLength}`. Over-limit query
is null and `needsShorter:true`: no truncation, omitted boundary, inferred scope
or silent source summarization. Unsupported interpretation instead returns
`needsClarification:true`. Preserve the full source snapshot when explaining a
length limitation; arbitrary long code ingestion is not implemented by this API.
`retrievalQuery` separately returns the compact specified aim/method/scope/rules
without unknown-state JSON scaffolding. It is a discovery query, not the full
meaning of the confirmed idea. Tests against actual registry records preserve
the original top two results for Fibonacci, Hill and language-comparison queries.

With `data/assistant.json.researchContract = "card-v1"`, the standalone interface
sends `{version:1, card, originalIdea?}` through `claim-research.js`. The card is
the active `ClaimShare.cardData` format: outcome, ordered operations and their
parameters, complete scope, all rule states, and unresolved constraints. The
server validates this structure and derives both retrieval and model context.
Caller-supplied query/page overrides are rejected. This validates data, not proof
that a human clicked Confirm or that an interpretation is semantically correct.

All selected manuscript pages (up to the complete 75-image collection) remain
explicit. Page IDs are separate retrieval hints rather than repetitive ranking
text. Passage qualifiers, non-page targets, missing values and literal method
parameters remain intact; page membership still does not prove executed coverage.
Structured parameter values participate in retrieval even when a short operation
label does not mention them. No procedure-equivalence inference is made.

The original human wording is separate and exact. Imported share-link summaries
are not passed off as original wording. Edit history, material metadata and prior
results are not active card fields; this route does not analyze attached files.
Limits remain 12,000 card bytes, 32,000 request bytes, 1,500 discovery characters
and 6,000 model-context characters. An 8,000-character original-text ceiling is
also checked, subject to the stricter combined context limit. Nothing is silently
truncated. Nonempty unresolved constraints still block comparison under the claim
model's existing readiness policy.

`ClaimResearch.binding(request)` hashes the canonical active card and supplied
original wording. Every accepted-card response, including no-match and cached
responses, echoes this SHA-256 binding. The browser verifies it before displaying
findings or a no-match conclusion. Cache identity includes that binding, model and
prompt version, derived queries, exact page hints and complete selected evidence.
The full client confirmation revision remains separately bound to the print packet.

The legacy `{query, confirmedQuery?, pages}` API remains available to old clients;
its two-page optional hint limit is unchanged. It does not offer card validation
or response binding. Deploy the updated Worker before enabling the new config.

`bindResearch` retains the exact local confirmation and published evidence;
`packetSnapshot` rejects a mismatched revision. Printing reuses this packet and
never makes a second model call. Retrieval remains candidate discovery: full
record evidence is preserved, but prose scopes do not form an automatic proof of
containment, equivalence, novelty or exhaustion.

There are 321 published records at this review. Every record has `scope.pages`,
`representation`, `procedure`, `parameters`, `exclusions`; 212 have `artifacts`.
Most consequential settings are prose. Some nominal page sets include partly
scored pages, and family/variant membership does not prove equivalent inputs,
reset state or evaluated configurations. No automatic containment/union matcher
is implemented. Empty retrieval cannot establish novelty. Measurement/audit/
control/replay types must not become solved-method evidence through the claim
model. A changed evaluation may reuse outputs, but this API does not infer that
they are complete or available.

## Checks

`node scripts/test_claim_specification.cjs` passes 15 grouped tests, including
browser UMD loading, arbitrary source fidelity, all four field states, scope
holes, three different boundary meanings, dependent-rule revalidation, compound
operation preservation, unsupported Other, nested unknowns, immutable prior
confirmations, no execution through confirmation, bounded nontruncating research
queries, current published evidence preservation and stale packet rejection.
No hosted inference, network fetch, new manuscript computation or fixture
research is used by these Node tests.

## Standalone surface

`investigate.html`, `investigate.js`, `investigate.css` implement capture,
consequential clarification, editable tagged confirmation, comparison and print.
Known reversal wording gets concrete choices. Other methods remain editable
supplied wording without guessed cipher semantics. User edits carry clarification
provenance separately from original text. File/image extraction is not offered.
Legacy `?q=` is prefilled without submission; valid repeated/comma-separated
`pages` hints enter scope explicitly without changing the original wording.

The current tab keeps a bounded draft in session storage for refresh recovery.
It is matched to the exact entry URL, so a different incoming idea or shared link
takes precedence. Original text, clarification choices and unsubmitted editor
values remain separate. Restoring a card always returns it to unconfirmed review;
results and in-flight requests are not resumed. Disabled
storage leaves the normal flow usable, and corrupt, oversized or expired saved
drafts are ignored. Recovery sends no interpretation, research or save request.

A separate, bounded 24-hour session entry retains the exact confirmed intake
body and request ID. After refresh, explicit reconfirmation retries that same ID
only when both the standardized card and original wording are unchanged. A
changed card or original receives a new ID. Stored receipts are hints, not proof
of saving: the server must acknowledge the retry before the UI reports Saved.
Restoring, editing or opening a shared card never submits it automatically.

The real registry and endpoint configuration load in parallel. Optional manuscript
context times out separately and does not gate confirmation or rerender an input
or editor. Request-local controllers and revision guards prevent canceled/late
responses or old timeouts from corrupting a later result. Canceling an edit
restores the same confirmed result and packet. Source/citation links open new
tabs to preserve the working result. Response ID/href and **full source text**
must match loaded evidence; changed-source responses are rejected instead of
printing a different version. Safe Markdown rendering escapes untrusted content.

`node scripts/test_investigate.cjs` passes helper/retrieval groups and two
mocked event-DOM journeys, including success→packet→print→edit/cancel, cancel/
retry, stale responses, request-local timeout, source binding and optional-context
races. All model responses are mocked; evidence is from the actual registry.

`node scripts/preview_investigate.cjs` starts a localhost-only preview on4397 with
a fail-closed injected fetch mock. It never needs hosted inference. QA variants
`?qa=offline`, `empty`, `delay` and `changed` exercise recovery conditions. This
server must not be used for production. CUA rendered the actual interface at
320,390,768,1440 pixels without horizontal overflow, and exercised ambiguity,
boundary choice, confirmation, mocked sourced result, edit and cancel. The
browser print dialog/PDF pagination was not verified; Node tests prove the print
markup derives from the same frozen reviewed packet. A desktop screenshot is
stored outside the repository at `../investigate-qa-1440.png`.

### Conservative compound interpretation

Initial interpretation recognizes complete small reversal forms, not substrings
inside arbitrary prose. An explicit `then` may separate a recognized operation
from one opaque tail; every later key, step and qualifier stays verbatim in that
tail. It does not split quoted key contents or claim to parse the remaining
cipher. If wording includes negation, conditions, exceptions, uncertain order or
code, the full supplied method remains visible without inferred positive rules
or an inferred scope that could mistake an excluded page for a target. Other
unrecognized attachments likewise remain in the method wording.

Each ambiguous operation has an explicit operationIndex. A choice replaces only
that piece and preserves its sourceText, existing parameters and all sibling
operations. Tests cover Vigenere key FOO and resets after digit reversal, an
ambiguous reversal followed by Vigenere and rotation, quoted `FOO then BAR`, and
ten negation/exception/uncertain-order forms. These checks prevent a row-only
retrieval result from silently answering a compound proposal.

### Conditional aim and scope questions

The standalone flow now asks missing aim and scope before confirmation, after
any consequential operation/boundary ambiguity. Outcome choices come from the
shared registry, with an unclassified explanation or undecided answer; scope offers
the bounded unsolved LP2 set, exact pages/passage and undecided. Nothing is
preselected. A custom passage remains exact prose rather than pretending to be
a whole-page selection. The unsolved choice explicitly selects LP2-00–55;
undecided leaves the original field unspecified. A recorded undecided answer
prevents repeated questioning without turning unknown into all material.

Only confident positive source goal forms are recognized; negative/opaque goal
wording is not assigned a positive aim. Supplied exact page lists and explicit
all-unsolved scope are retained rather than reasked. A question is the main
heading with choices immediately below; tags appear when the questions are
resolved. This is not an execution questionnaire: missing transcription version,
evaluation and other protocol parameters remain secondary requirements.

The compact scope renderer coalesces only consecutive pages of one release.
It leaves gaps and release changes explicit and never changes the confirmed
page array. An unrelated interpretation edit preserves a custom passage scope.
Additional tests cover no-match findings/packet/printing and edit restoration,
and ensure generic aim wording does not derail strong technique retrieval.

### Proposed interpretation before review

Release status (24 October): enabled after deploying Worker version
`7564f79f-305b-45a0-9f53-8f9c8e99a527` and verifying a production synthetic request.
Its measurement aim, ordered instructions, page-list gap and shuffle count were
preserved. Captured-response replays cover literal keys, excluded pages and a
method-only idea whose aim must remain unknown. Validation checks structure and
source evidence, not complete extraction or semantic correctness. Visitors still
review and confirm the proposed card.

`claim-interpretation.js` is the shared browser/Worker validator and draft adapter;
`services/idea-assistant/interpretation.mjs` preserves its ESM interface. The
`/interpret` endpoint proposes a candidate only after an explicit idea submission.
The frontend enables it through `interpretationEndpoint` in `data/assistant.json`.
Imported cards and interpretation edits never trigger it. Research comparison and
saving still require the separate confirmation action.

Interpretation waits for endpoint configuration, not for the experiment registry.
A slow or failed registry must not prevent clarification or editing. The research
confirmation action remains disabled until valid published records and their
snapshot identity are available. Registry retries update availability without
replacing the active form, changing the original wording or requesting another
interpretation. A configuration failure offers the original-wording path.


Each extracted field cites an exact source substring. The handler locates a
uniquely occurring quote directly in the original; repeated quotes still need a
correct supplied offset. It never changes quoted wording, steps or parameters.
The shared validator checks controlled categories, operation order, literal keys,
scope and consequential ambiguity before constructing a draft. Missing values
remain unknown; uncovered wording stays visible. These checks establish source
provenance and structural consistency, not semantic correctness. The user still
reviews and confirms the interpretation.

The model uses a separate strict wire schema containing ordered instruction
quotes, scope wording and explicitly stated rule quotes. The adapter derives
literal keys and inclusive page ranges from that evidence; it does not ask the
model to generate keys, page arrays or rule defaults. Multiple keys remain in the
full instruction, without arbitrarily selecting one. Qualified or alternative
page selections must retain their complete wording. Rule states such as
“unrestricted” require an explicit statement about that particular rule. Duplicate
rules, unsupported classifications and invented fields fail validation.

Literal key contents cannot create outcome, scope or rule evidence. For example,
a key named “IF” is not a condition and a key named “LP2-15” does not select that
page. The offline corpus covers 26 idea shapes alongside validator, browser
parity, handler and frontend journey checks. It tests proposed candidates rather
than claiming live model accuracy.

Known outcome categories need explicit supporting aim wording. A cipher name alone
does not establish a deciphering aim. Unsupported guesses become unknown without
changing the method, scope or original text. A complete later page exclusion can
qualify scope separately from an explicit aim; negated or conditional aims cannot
be turned positive by extracting a substring. Broad named material remains a
literal selection rather than an invented list of pages.

The response carries the SHA-256 of the exact original text; the browser checks it
and independently validates the candidate. Cancel, fallback, new input and leaving
the flow invalidate outstanding replies. A failure offers retry or continuing with
the original wording, without inventing a successful interpretation. The model
never supplies the saved original text.

One uncached interpretation makes at most one model call, with a 20-second response
deadline and no automatic repair or retry. Exact inputs share pending work and a
bounded 10-minute cache. The existing six-requests-per-minute binding is shared
with comparison; a successful uncached journey can therefore use two generations.
Interpretation has three provider slots, and a timed-out provider retains its slot
until it actually settles. These bounds limit work; they are not a global daily
quota. The frontend waits at most 30 seconds and keeps the original on failure.


## Candidate discovery from confirmed operations

`ClaimResearch.prepare` and Worker-side validation derive search hints from the
active card. Visitors cannot supply a separate discovery override. Supported
row reversal retains the confirmed boundary choice: rune order within a row,
rune order within a word, or word order within a row. Opaque, conditional and
negated wording does not acquire a positive operation merely from a keyword.

Published records may carry reviewed `discovery` operation and evaluation hints.
These select candidate evidence; they do not establish identical settings or
executed coverage. Prefer the same operand and extent. A page-wide word-order
test may be a related lead for a row-wise proposal, but its full scope must
still explain that difference. Single-step searches can include a second
evaluation; compound searches select a lead per ordered step before extra
variants. They keep at most four complete records within the existing 9,000
character research budget. Unrepresented steps remain unanswered, not tested.

Metadata is currently audited for four reversal/route records. Other operations
retain lexical retrieval. The shared selection code powers both the Worker's
evidence and the browser's fallback records; neither source text nor the
confirmed idea is rewritten. `scripts/test_claim_discovery.cjs` covers operand
distinctions, full/compact parity, compound selection and refusal boundaries.
