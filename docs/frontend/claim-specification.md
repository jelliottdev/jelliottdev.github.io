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

The standalone interface sends `{query: compactQuery, confirmedQuery: fullQuery,
pages}`. Its compact discovery query is limited to 1,500 characters and the full
confirmed query to 6,000, matching the accompanying Worker adaptation. Both are
derived from the same immutable snapshot, and stale responses are discarded.
The server sees explicit confirmed wording, not a validated confirmed object;
do not claim server enforcement of confirmation. The page parameter cap is
**two**. Never slice a larger exact
set: either explicitly support it in the service or omit the optional page hint
as a whole while retaining the full scope in the untruncated query. The latter
only preserves lexical context, not a structured page-coverage guarantee.

Future server contract adaptation:

1. Accept a versioned confirmed snapshot, validate bounded JSON and schema with
   `validateConfirmed`, and derive the research query server-side. Raise the
   current 32,000-byte body / 1,500-character discovery query / 6,000-character context limits only through an explicit
   bounded request-budget decision; do not truncate snapshots.
2. Preserve exact selected page sets, unknowns, non-page targets and positional
   selections. Current `readQuery()` only accepts query + at most two page IDs;
   it cannot receive this richer claim unchanged.
3. Keep retrieval as candidate discovery. Current `experimentDocs` preserves
   full scope, family, variant, finding and limitations, but these are not a
   machine-verified executed-configuration relation. Include record type and
   exact source fields in the prompt; ask for difference-first bounded findings.
4. Cache on prompt/model version, exact confirmed binding and exact selected
   evidence. Return the claim binding with every response. Query-only identity
   is insufficient when source provenance/revision or consequential fields differ.
5. Bind reviewed answers with `bindResearch(snapshot,{id,at,evidence,answer,
   openQuestions,proposedTests})`, using actual published records including scope,
   finding and limitations and a registry snapshot ID/hash. It preserves the
   full evidence and marks proposed tests `not_run`. It does not generate claims.
   Snapshot dates are caller-supplied; use exact registry content hashes.
6. `packetSnapshot(snapshot,result)` rejects a mismatched revision/binding and
   serializes the same confirmed claim/evidence/answer. Printing must render this
   object, never make a second model call or strengthen its conclusions.

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
