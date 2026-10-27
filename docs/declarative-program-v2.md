# Declarative rune programs, version 2

Status: private integration tested; the public idea-to-experiment UI is not yet connected.

The old runner preserves rune positions. It cannot represent removing filler
runes without changing its evidence contract. Version 2 is a separate task,
engine, result and control-suite version; existing version-1 receipts are never
converted or reinterpreted.

## Implemented boundary

- `declarative-rune-program.js` accepts bounded data, never generated JavaScript.
  Existing exact operations compose with literal rune-type removal and explicit
  repeat collapse. Collapse declares both its grouping boundary and whether
  `AAA` becomes `A` or `AA`. Non-rune characters remain in place relative to
  surviving characters.
- Result alignment names retained original character slots and removed slots.
  It is **not value-origin or dependency provenance** after reversal or feedback.
- `declarative-plan-controls.js` calculates expected synthetic outputs, alignment,
  metrics and maintained evaluations independently. Its fixtures do not execute
  the target manuscript inputs. Passing them is a calculation check, not a test
  of filler or decryption hypotheses.
- `local-experiment-dispatch.js` routes exact schema/engine pairs. Version 1
  delegates unchanged. Version-2 inspection requires the dispatcher's verified
  result object; a copied result is not a certificate.
- `local-run-executor.js` selects a separate fixed worker for version 2. Batch
  workers are reused only within their version and replaced when it changes.
  The old worker and its import path remain unchanged.
- `declarative-program-description.js` explains the actual typed operations and
  illustrates them using invented input. It does not infer a key source from a
  title or turn proposed evaluations into supported ones.
- `method-implementation.js` binds a separate program draft to the exact
  structured proposal. Coverage must account for every step, parameter, control,
  evaluation, representation and key-use statement. Ordered steps cannot be
  silently reversed; one program cannot claim multiple parameter alternatives.
  Complete coverage remains a proposed mapping, not proof of faithful meaning.
- The implementation draft handler, review component and preparation workspace
  preserve unsupported parts and never supply a missing evaluation. They are
  separate from task creation and execution.
- `method-implementation-origin.mjs` reconstructs the reviewed implementation
  from the official aggregate during preparation and fresh authorization.
  Preparation receipts bind the original card, program, full scope, source
  edition and independent control suite. Version-two tasks cannot borrow a
  legacy preparation authority or authored origin.
- The task persistence path saves and independently replays shortened outputs
  and their alignment. Shared legacy evidence and expansion paths remain closed
  to version two. Device recovery and result views use the exact version
  dispatcher; raw or self-hashed results cannot become verified findings.

## Required before public admission

The structured method proposal is intent, not executable authority. Do not parse
its prose, choose a neighboring method, or substitute a supported measurement for
an unsupported evaluation just to make it runnable.

1. Connect the drafted implementation and review components to the saved idea
   and runnable task screens. Test the live model's schema support and ability
   to preserve missing scientific evaluations, not only mocked responses.
2. Verify the full visitor path: saved idea → implementation review → controls →
   local run → explicit save → reload and independent replay. No automatic
   execution or public test records during software verification.
3. Add version-2 computation evidence and pinned reproduction sources. Leave
   old evidence, archive and reuse paths closed until their contracts support it.
4. Measure maximum-size execution and verification in the deployed verifier's
   memory budget, including the submitted result and request overhead. A passing
   Node heap probe does not establish that a Worker isolate has enough memory.

This engine supports new compositions of its declared primitives. It does not
yet support arbitrary newly invented algorithms, random-null significance tests,
or automatic expansion of every experiment. Those remain implementation work.
