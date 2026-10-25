"""Reproduce an authored language comparison after both maintained control suites.

python verify_authored_language.py --task task.json --origins origins.json --controls runner-controls.json --out results.json
Only fixed sibling modules and the Python standard library are used. No network.
"""
import argparse
import json
from pathlib import Path
import re

import research_runner as runner
import verify_controls as authored
import verify_plan_controls as generic


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', type=Path, required=True)
    parser.add_argument('--origins', type=Path, required=True)
    parser.add_argument('--controls', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        target, origins, controls, output = (p.resolve() for p in
                                             (args.task, args.origins, args.controls, args.out))
        runner.require(target.parent == origins.parent == controls.parent,
                       'Task, origins and runner controls must share one extracted folder')
        runner.require(not output.exists() and not args.out.is_symlink(), 'Output already exists')
        inputs = (target, origins, controls, Path(__file__).resolve(), Path(runner.__file__).resolve(),
                  Path(authored.__file__).resolve(), Path(generic.__file__).resolve(),
                  target.parent / 'language-model.json')
        runner.require(output not in inputs, 'Output cannot overwrite packaged inputs or guards')
        task = authored.read_json(target)
        runner.validate(task)
        runner.require(task['criterion']['kind'] == 'language-score', 'An exact maintained language comparison is required')
        original = authored.read_json(origins)
        authored.verified_controls(task, original, target.parent)
        generic.verified_controls(task, authored.read_json(controls))
        # Neither suite executes the target; all controls must finish first.
        result = runner.run(task)
        payload = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n'
        with output.open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(payload)
        print('Verified authored and task-bound controls; saved results to ' + str(args.out))
    except (OSError, ValueError, TypeError, RecursionError) as error:
        parser.exit(2, 'verify_authored_language: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
