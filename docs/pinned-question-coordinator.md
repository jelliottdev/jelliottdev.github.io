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

1. **Renew an expired unfinished scan.** Current cursors expire after 48 hours.
   Add a server-owned logical-question head pointing to versioned scan attempts.
   Authenticate the stored cursor before identifying expiry; corruption is not
   permission to reset. Start a fresh attempt in a separate bounded transaction,
   preserving the same verified coverage and original public question. Retain old
   journals. Keep the head revision monotonic so stale clients cannot match a new
   attempt's revision zero. Completed receipts do not rotate merely for expiry.
2. **Admit only missing work.** Before preparing the next bounded calculation,
   check for results saved after the original discovery snapshot. Preserve the
   original parent association through the controlled-member admission bridge.
   A scheduler selection is not execution authority.
3. **Connect one persistent workspace.** Intercept supported complete questions
   before `run.js` sends finite settings to the existing, smaller-domain runner.
   Keep one parent URL and one Run/Resume action. Reuse the controlled browser
   executor and existing result-save endpoints. Recover a pending save or import
   before preparing another job. A timeout may leave a committed transaction;
   refresh durable state rather than assuming nothing happened.
4. **Provide a real entry point.** The source record needs explicit actions for
   the two maintained complete searches. Do not create public questions for each
   scheduled member. Keep unrelated finite searches on their existing path.

The new HTTP handler must precede the broad `/ideas` handler, load the exact
canonical public parent, and forward only explicitly supported actions. Enable
configuration and apply migrations only alongside the working public flow.

## Request limits and verification

The current SQLite integration tests measure fresh service factories plus one
operation: 47 statements for discovery of twelve original 75-page receipts, and
31 for importing twelve selectors from one original. The future parent lookup,
head handling, and outbound fetches must be measured together before enabling
the handler; module-level budgets do not establish a whole-request budget.

Keep discovery, import, controls/admission, and execution/result saving in bounded
requests under one user intent. Do not raise the ordinary finite compiler's
limits to accommodate a complete search.

`test-pinned-question-coordinator.mjs` covers real SQLite restart, crash, races,
tampering, generation changes, delayed work, and accepted completion after expiry.
It uses invented local outputs and does not run manuscript experiments. Public
integration also needs expiry-attempt recovery, full browser save/retry/resume,
rate-limit recovery, and measured end-to-end request budgets.
