"""Create a draft, optionally using --baseline existing-record-id."""
import argparse
import json
import re
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('id')
parser.add_argument('--baseline', help='Published family baseline whose scope the draft starts from.')
args = parser.parse_args()
if not re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', args.id):
    parser.error('Use a lowercase hyphen-separated ID starting with a letter.')
root = Path(__file__).resolve().parents[1]
target = root / 'experiments/records' / args.id
if target.exists():
    parser.error('That ID already exists; no files were changed.')
record = {
    'schema': 'liberpedia-experiment-v2',
    'id': args.id, 'title': '', 'status': 'draft', 'question': '', 'tags': [],
    'family': {'id': args.id, 'title': '', 'question': '', 'baseline': args.id},
    'variant': {'label': 'Baseline', 'changes': []},
    'scope': {'pages': [], 'representation': '', 'procedure': '', 'parameters': '', 'exclusions': ''},
    'outcome': 'inconclusive', 'result': {'finding': '', 'limits': '', 'next_steps': ''},
    'analysis': '',
    'reproduction': {'command': f'python experiments/records/{args.id}/run.py',
                    'environment': '', 'script': f'experiments/records/{args.id}/run.py',
                    'script_sha256': '', 'inputs': [], 'outputs': []},
    'review': {'reviewer': '', 'retested_on': '', 'kind': '', 'human_review': 'pending'}, 'sources': [], 'related': []
}
if args.baseline:
    if not re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', args.baseline):
        parser.error('The baseline must be a record ID, not a path.')
    baseline_path = root / 'experiments/records' / args.baseline / 'record.json'
    try:
        baseline = json.loads(baseline_path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        parser.error('The baseline record could not be read; no files were changed.')
    family = baseline.get('family', {})
    if (baseline.get('id') != args.baseline or baseline.get('status') != 'published'
            or not isinstance(family, dict) or family.get('baseline') != args.baseline
            or not all(isinstance(family.get(key), str) and family[key].strip()
                       for key in ('id', 'title', 'question', 'baseline'))
            or not isinstance(baseline.get('scope'), dict)):
        parser.error('Choose a published family baseline, not a draft or sibling variant.')
    record['family'] = family
    record['scope'] = baseline['scope']
    record['variant'] = {'label': '', 'changes': []}
    record['related'] = [args.baseline]
record['analysis'] = '''## Question
State one testable question.

## Rationale
Explain why this question is worth testing. Link the observation or earlier work that motivated it.

## Scope
Specify pages, input representation, transformations, parameter ranges, and exclusions.

## Plan before running
Record the planned input hashes, candidate count, success criterion, and stopping rule.
Separate choices fixed before inspection from exploratory choices.
For random sampling, specify the seed, trial count, null model, and uncertainty calculation.

## Method
Explain each step, the controls, and the decision criteria.

## Reproduce
Give the command, dependencies, inputs, and expected output.

## Results
Record actual output with units, counts, and links to machine-readable results.
State how many cases completed, which failed, and whether the run reached its planned stopping point.
Do not fill this section with expected or invented results.

## Changes after inspecting results
Record changed boundaries, exceptions, scores, or parameter ranges and why they changed.
Keep prior outputs identifiable. Write "None" only if no changes were made.

## Retest
Identify the reviewer, retest date, command, and exact outputs compared.
Leave this unfinished until a retest has actually happened.

## Interpretation and limitations
Separate what the run shows from what remains untested.

## Related work and sources
Link earlier records and primary evidence; explain what differs.
'''
if args.baseline:
    record['analysis'] += f'''
## Comparison with the baseline
Baseline: [the existing record](#/experiments/{args.baseline}).
The draft starts with that record's scope. Describe the proposed change before running.
For each changed scope field, fill variant.changes with its exact before and after values
and explain the reason. Do not copy the baseline's finding or review into this record.
An identical rerun belongs with the original record rather than a new published variant.
'''
target.mkdir(parents=True)
(target / 'record.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
(target / 'run.py').write_text('''"""Draft only. Replace with a documented reproducible experiment."""
raise SystemExit("No experiment implemented. Complete and retest before publication.")
''', encoding='utf-8', newline='\n')
print('Created draft:', target)
print('Author the question, result and analysis in record.json; implement run.py, then use the central publication command.')
if args.baseline:
    print('Inherited family and scope only. Declare the changes, inputs, plan and review separately.')
