# Complete-question work coordinator

This is an internal integration contract, not a public feature. The coordinator
currently handles discovery and import of prior evidence. It does not admit or
run a new calculation, publish an idea, or conclude that an idea failed.

## Authority and recovery

`createPinnedQuestionCoordinator(questionToken, dependencies)` accepts the private
canonical-question token. Request bodies must never supply its source, bank,
partition, discovery service, coverage service, cursor, or completion proof.
`createPinnedDiscoveryCoordinator` is a trusted composition/test seam, not an HTTP
request adapter.

The interface is `read()` and `advance({expectedRevision})`. Each HTTP invocation
should perform one operation. The client may display returned progress, but it
cannot replace the durable server frontier.

A stable server-owned head points to the active scan attempt. Public revisions
remain monotonic across attempts. Only authenticated expiry can renew an unfinished
scan; renewal is one bounded transaction and retains the same verified coverage,
original question, and immutable history. A corrupt token cannot authorize renewal.

The coordinator moves through discovering, importing, verifying, and ready:

- Discovery retains compact original-source references and exact selectors.
- An import request processes one original source and at most twelve selectors.
- The discovery cursor advances only after every selector on that page imports.
- A crash after the coverage transaction retries the same import idempotently.
- A separate final verification writes an immutable accepted completion receipt.

Immutable page and commit journals bind the frontier. A trigger-maintained summary
keeps reads independent of the number of earlier pages. Completed receipts remain
valid after temporary cursor expiry, subject to the current source, evidence
epoch, verifier, and published registry generation.

`lookupCompleted` means the original snapshot was completely searched and its
returned results imported. It does not mean all possible calculations ran, no
later result exists, or the hypothesis is false. `negativeConclusion` stays false.
The verified coverage view separately exposes an indexed matching-opening source.
That positive result can stop this exact opening check while coverage remains
incomplete; it does not establish a complete manuscript reading.

## Gates before public integration

1. **Admit only missing work.** Before preparing the next bounded calculation,
   check for results saved after the original discovery snapshot. Preserve the
   original parent association through the controlled-member admission bridge.
   A scheduler selection is not execution authority.
2. **Connect one persistent workspace.** Intercept supported complete questions
   before `run.js` sends finite settings to the existing, smaller-domain runner.
   Keep one parent URL and one Run/Resume action. Reuse the controlled browser
   executor and existing result-save endpoints. Recover a pending save or import
   before preparing another job. A timeout may leave a committed transaction;
   refresh durable state rather than assuming nothing happened.
3. **Provide a real entry point.** The source record needs explicit actions for
   the two maintained complete searches. Do not create public questions for each
   scheduled member. Keep unrelated finite searches on their existing path.

The HTTP adapter loads the exact canonical public parent. It supports one bounded
read, discovery advancement, preparation, original-receipt import, or saved-result
credit per request. It is registered before the broad `/ideas` handler; the browser
path is still disabled in site configuration pending sustained deployment
verification. Migrations 0019–0023 are applied.
Unsupported questions retain their existing flow; source outages must remain
errors rather than being mislabeled unsupported.

## Request limits and verification

The current SQLite integration tests measure fresh service factories plus one
operation: 47 statements for discovery of twelve original 75-page receipts, and
31 for importing twelve selectors from one original. Initial head creation adds
two statements; later requests replace registration with a head lookup. The HTTP
parent lookup and outbound fetches must also be measured before enabling the
handler; module-level budgets do not establish a whole-request budget.

Keep discovery, import, controls/admission, and execution/result saving in bounded
requests under one user intent. Do not raise the ordinary finite compiler's
limits to accommodate a complete search.

`test-pinned-question-coordinator.mjs` covers real SQLite restart, crash, races,
tampering, generation changes, delayed work, and accepted completion after expiry.
It also covers unfinished-attempt renewal, preserved coverage/history, monotonic
revisions, and competing or failed renewal transactions. It uses invented local
outputs and does not run manuscript experiments. Public integration still needs
full browser save/retry/resume, rate-limit recovery, and measured end-to-end
query, outbound-request, row-read, CPU, and memory budgets on the deployment.

## Prepared work and device recovery

`createPinnedQuestionJobs` accepts the same private original-question token. The
server selects the first missing setting and at most twelve pages, checks current
evidence, and issues the existing controlled preparation under the unchanged
public parent. A fresh check also guards task admission. A signed short-lived
import token names an exact original source and selected intersection; importing
is a separate independently verified operation. `recordSaved` requires the actual
persisted result, immutable preparation, and original-parent task association.
Shared task ownership does not change that association.

`pinned-question-workspace.js` preserves one parent URL and requires an explicit
Run and save action. It retains device output and saved references until credit
succeeds. Recovery checks existing saved results before creating or running work;
a saved reference skips task creation entirely. Pause cancels the executor and
network reads, including a transport that ignores abort. No page-load calculation
is authorized by loading progress.

The independent jobs suite uses actual SQLite, synthetic text, independently
constructed controls, and the real coverage/discovery/source services. The
trusted composition seam cannot make invented inputs eligible for the maintained
production registry. Production admission is separately checked with synthetic
controls and no new manuscript result. These local tests do not establish hosted
CPU, memory, outbound-request, or whole-job HTTP budget headroom.

## Deployment gate: sustained requests, not isolated success

The full-search links remain disabled in `data/assistant.json`. Two maintained
parent questions are published with no calculation tasks; their pages remain
read-only while this gate is closed. Publication is not evidence that execution
is available.

Live verification found a failure that local correctness and SQL budgets did
not detect. On Worker version `de38cfa5-0038-4b62-b725-cf34b8691d95`, isolated
reads and discovery steps returned 200, but a sustained discovery request was
terminated with `exceededCpu` after 217 ms. Earlier requests received temporary
CPU flexibility; their larger successful timings are not a usable budget. The
account's billing plan has not been independently established.

Before enabling a complete search:

- Measure cold and sustained requests for every operation, including source
  binding, preparation, admission, import and credit. Count the complete HTTP
  request, not only the final service call.
- Require headroom within the actual configured hosting budget. Do not retry CPU
  failures to force progress or infer capacity from transient burst allowance.
- Verify browser pause, rate-limit waiting and saved-output recovery. A failed
  request must preserve original question identity and existing work.
- Keep unsupported work distinct from a service outage. Never route a complete
  question through the smaller generic runner merely because its endpoint is off.

Repeated source parsing, bank scans and full-parent construction are shared
costs. Move immutable verified work out of repeated request paths, with exact
source invalidation and independent parity tests. Cache no mutable coverage,
receipts, admission decisions or execution authority. The eventual compiled
source artifact must preserve the same source, card, domain and control bindings.

The production HTTP budget fixture currently checks preparation (24 SQL
statements, nine fetches) and fresh task admission (19 statements, sixteen
fetches), using synthetic controls and no new manuscript calculations. These are
useful limits, but do not establish live CPU capacity or a successful full loop.

The current implementation batches detached page hashes, reuses verified parent
snapshots within a four-entry/1 MiB bound, and memoizes the exact frozen default
archive fingerprint. Every source-cache hit still captures and compares complete
domain/source bytes, checks native crypto identity, and issues a fresh private
planning token. Custom crypto and injected registries bypass shared memoization.
Warm local GET CPU dropped from roughly 594 ms to 15–47 ms across profiling
runs; cold requests remain much more expensive. These measurements justify the
optimization, not feature activation.

## Compiled deployment inputs

Fixed parent planning and default archive metadata are now compiled before
shipping the Worker. They are private deployment assets, not browser-supplied
plans or evidence. Regenerate in this order when their dependencies change:

```
node scripts/build_pinned_parent_artifacts.mjs --write
node scripts/build_compiled_program_index.mjs
node scripts/build_evidence_registry_fingerprint.mjs
```

Each builder has a `--check` mode enforced by the Node manifest. Compilation
checks the existing planner, all source pins, and the independent manifest
format; it runs no manuscript calculations. Parity tests compare all 5,122
setting identities, both complete page scopes, and the existing catalogue and
registry fingerprints. Compiler text pins use explicit UTF-8/LF normalization;
scientific data, official aggregate bytes and control manifests retain exact
byte hashes.

A default request fetches the official input aggregate afresh and verifies its
complete raw-byte hash before receiving a new private planning token. It also
checks the complete maintained domain/template/manifest binding. A changed
Pages asset and an older Worker therefore fail closed, in either deployment
order. There is no stale-plan fallback. Injected source loaders, explicit bundles
and custom crypto retain the ordinary full validation path.

The default source loader can omit repeated manifest parsing only after a fresh
native hash and the complete registered source binding match the build-checked
manifest. Other sources retain ordinary parsing. Selected Warning controls,
ordinary controls, receipt replay, source selection, evidence epochs, generation
fences and admission checks remain live. Compiled assets contain no tested-case
counts, results, lookup completion or execution permission. Their build hash is
not a new semantic question/coverage identity, so an equivalent compiler update
does not discard saved work.

This removes repeated whole-parent and fixed-index validation from cold
requests. It does not prove the complete loop fits the deployment CPU budget.
Selected-key expansion and controlled preparation still require measured cold
and sustained verification before the existing feature gate can be opened.
