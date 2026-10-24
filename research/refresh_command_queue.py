"""Refresh internal command triage from reviewed scopes, without inferring readiness.

Run after changing public-attempt-reconciliation.json. This does not execute a
source command, create a research record, or put operational UI on the website.
"""
import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = Path('research/execution-ready-queue.json')
REVIEW = Path('research/public-attempt-reconciliation.json')


def unique(rows, key):
    found = {}
    for row in rows:
        identifier = row[key]
        if identifier in found:
            raise ValueError(f'Duplicate {key}: {identifier}')
        found[identifier] = row
    return found


def refresh(queue, review, records, review_sha256):
    result = copy.deepcopy(queue)
    if queue['source']['ledger_sha256'] != review['source']['ledger_sha256']:
        raise ValueError('The command audit and review use different source ledgers')
    reviews = unique(review['entries'], 'source_id')
    published = unique(records, 'id')
    commands = unique(queue['command_audit'], 'source_id')
    rows = []
    for identifier, original in commands.items():
        if identifier not in reviews:
            raise ValueError(f'Command missing from current review: {identifier}')
        reviewed = reviews[identifier]
        initial = original.get('initial_assessment')
        if initial is None:
            initial = {k: v for k, v in original.items() if k not in (
                'source_id', 'reproduce_command', 'source_evidence',
                'ledger_status', 'ledger_control')}
        row = {k: copy.deepcopy(original[k]) for k in (
            'source_id', 'reproduce_command', 'source_evidence',
            'ledger_status', 'ledger_control')}
        row['initial_assessment'] = copy.deepcopy(initial)
        links = copy.deepcopy(reviewed.get('record_links', []))
        execution = copy.deepcopy(reviewed.get('execution_replay'))
        ids = {link['record_id'] for link in links}
        if execution:
            ids.update(execution.get('record_ids', []))
        for record_id in ids:
            record = published.get(record_id)
            if not record or record.get('status') != 'published':
                raise ValueError(f'{identifier}: unpublished/missing record {record_id}')
        row['current_review'] = {
            'status': reviewed['status'],
            'record_links': links,
            'execution_replay': execution,
            'remaining_scope': copy.deepcopy(reviewed.get('unresolved_parts', [])),
            'whole_entry_coverage_verified': reviewed.get('whole_entry_coverage_verified', False),
        }
        rows.append(row)
    if 'initial_counts' not in result:
        result['initial_counts'] = copy.deepcopy(queue['counts'])
    result['schema'] = 'liberpedia-execution-ready-queue-v2'
    result['counting'] = (
        'One row is one original ledger entry with a reproduction command, not '
        'one idea or one remaining experiment. Current review is copied from '
        'the scope reconciliation; initial_assessment is historical. A complete '
        'executed grid does not close the wider method. Neither a linked record '
        'nor a partial status establishes that a follow-up is ready to run.')
    result['command_audit'] = rows
    result['counts'] = {
        'reproduction_command_entries': len(rows),
        'entries_with_published_record_links': sum(bool(r['current_review']['record_links']) for r in rows),
        'entries_with_remaining_scope': sum(bool(r['current_review']['remaining_scope']) for r in rows),
        'review_statuses': dict(sorted(collections.Counter(r['current_review']['status'] for r in rows).items())),
        'execution_replay_states': dict(sorted(collections.Counter(
            (r['current_review']['execution_replay'] or {}).get('state', 'not-recorded') for r in rows).items())),
        'explicit_priority_entries': len(result['priority_ready_source_ids']),
    }
    if not set(result['priority_ready_source_ids']).issubset(commands):
        raise ValueError('A priority ID is absent from the original command audit')
    result['current_review_source'] = {'path': REVIEW.as_posix(), 'sha256': review_sha256}
    result['reconciled_on'] = review['compiled']
    result['reconciliation_note'] = (
        'Refresh current_review from the named reconciliation after each published '
        'batch. Preserve the initial source/input audit separately. An empty priority '
        'list means no ready item is currently nominated here; it does not mean '
        'the archive or its remaining scopes are complete. Proposal-only entries '
        'without source commands remain in the full reconciliation.')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    review_bytes = (ROOT / REVIEW).read_bytes()
    records = json.loads((ROOT / 'data/experiments.json').read_bytes())['records']
    result = refresh(json.loads((ROOT / QUEUE).read_bytes()), json.loads(review_bytes),
                     records, hashlib.sha256(review_bytes).hexdigest())
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.check:
        if (ROOT / QUEUE).read_text(encoding='utf-8') != encoded:
            raise SystemExit('Command queue is stale; run python research/refresh_command_queue.py')
    else:
        (ROOT / QUEUE).write_text(encoded, encoding='utf-8', newline='\n')
    print(json.dumps(result['counts']))


if __name__ == '__main__':
    main()
