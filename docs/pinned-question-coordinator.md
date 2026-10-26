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

The staged HTTP adapter loads the exact canonical public parent and forwards
only read or advance. It is not registered in the Worker or enabled in site
configuration. Register it before the broad `/ideas` handler only alongside the
working public flow, its job-admission/save actions, and required migrations.
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
