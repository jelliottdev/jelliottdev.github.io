# Node validation

Run `node scripts/run_node_checks.cjs` from the repository root. The checked-in
`scripts/node-checks.json` manifest contains every unconditional Node check,
including required runtime flags. Add new checks there once, rather than adding
another workflow step. Append new checks after the frozen migration prefix;
the runner regression checks that the migration retained every original command.

The runner uses four separate processes with isolated temporary directories,
separate logs and bounded timeouts. A failed check does not skip the remaining
checks; any failure makes the batch fail. Checks that share external mutable
fixtures must declare the same resource name to serialize them. Avoid shared
checkout writes.

The workflow's separate scope step and scientific Python/build gates remain
unchanged. The Node batch is unconditional and must not use that scope output
to select a subset. Manual dispatch still runs full scientific validation.
