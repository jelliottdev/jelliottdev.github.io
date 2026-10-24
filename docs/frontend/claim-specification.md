# Claim model integration contract

Implemented only `claim-specification.js` and `scripts/test_claim_specification.cjs`.
No worker, UI, shared data or deployment was changed. The handoff's curated
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

Current browser-only integration may send the returned query to the unchanged
service, attach the result to its exact originating immutable snapshot, and
discard stale asynchronous results. The server in that mode sees the explicit
query, not a validated confirmed object; do not claim server enforcement of
confirmation. Current page parameter cap is **two**. Never slice a larger exact
set: either explicitly support it in the service or omit the optional page hint
as a whole while retaining the full scope in the untruncated query. The latter
only preserves lexical context, not a structured page-coverage guarantee.

Future server contract adaptation:

1. Accept a versioned confirmed snapshot, validate bounded JSON and schema with
   `validateConfirmed`, and derive the research query server-side. Raise the
   current 6,500-byte body / 1,500-character query limits only through an explicit
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
research was used.
