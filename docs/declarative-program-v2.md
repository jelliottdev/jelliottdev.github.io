# Declarative rune programs, version 2

Status: execution foundation, not yet a public idea-to-experiment path.

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

## Required before public admission

The structured method proposal is intent, not executable authority. Do not parse
its prose, choose a neighboring method, or substitute a supported measurement for
an unsupported evaluation just to make it runnable.

1. Translate into a separate bounded implementation draft, tied to the exact
   saved proposal hash. An AI may propose typed operations; their shape alone
   does not prove semantic agreement with the idea.
2. Derive the explanation and invented example from that program. Show key
   material separately from arithmetic, feedback and reset rules. Surface
   differences and unsupported conditions/evaluations before explicit review.
3. Bind reviewed implementation, original card/proposal, official input edition,
   exact page scope, task and independent controls in durable preparation
   authorization. Reconstruct and check the same binding at task creation.
4. Dispatch task/result saving and replay by exact version. Add version-2
   computation evidence and pinned reproduction sources. Leave old evidence,
   archive and reuse paths closed to version 2 until their contracts support it.
5. Verify the full visitor path: saved idea → implementation review → controls →
   local run → explicit save → reload and independent replay. No automatic
   execution or public test records during software verification.
6. Measure maximum-size execution and verification in the deployed verifier's
   memory budget, including the submitted result and request overhead. A passing
   Node heap probe does not establish that a Worker isolate has enough memory.

This engine supports new compositions of its declared primitives. It does not
yet support arbitrary newly invented algorithms, random-null significance tests,
or automatic expansion of every experiment. Those remain implementation work.
