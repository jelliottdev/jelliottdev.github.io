"""Select initial source reviews against the complete reconciliation register.

This is an internal batching aid, not a count of unfinished cipher experiments.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def select(ledger, reconciliation, requested=None, allow_reviewed=False):
    entries = {row['id']: row for row in ledger['entries']}
    reviews = {row['source_id']: row for row in reconciliation['entries']}
    if len(entries) != len(ledger['entries']) or len(reviews) != len(reconciliation['entries']):
        raise ValueError('Duplicate source IDs; repair the register before batching')
    if set(reviews) - set(entries):
        raise ValueError('Reconciliation contains IDs outside this source ledger')
    wanted = list(requested) if requested is not None else [i for i in entries if i not in reviews]
    if len(set(wanted)) != len(wanted) or set(wanted) - set(entries):
        raise ValueError('Requested IDs contain duplicates or unknown entries')
    repeated = set(wanted) & set(reviews)
    if repeated and not allow_reviewed:
        raise ValueError('Already reviewed: ' + ', '.join(sorted(repeated)) +
                         '. Use --allow-reviewed only for an intentional follow-up.')
    return [{'source_id': i, 'work_type': 'follow-up' if i in reviews else 'initial review',
             'current_review_state': reviews.get(i, {}).get('status', 'unreviewed'),
             'claim': entries[i].get('hypothesis', entries[i].get('claim', '')),
             'reproduction_command': entries[i].get('reproduce'),
             'evidence': entries[i].get('evidence', [])} for i in wanted]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ledger', type=Path, default=ROOT.parent / 'sources/dukotah-f08b20b/LEDGER.json')
    p.add_argument('--reconciliation', type=Path, default=ROOT / 'research/public-attempt-reconciliation.json')
    p.add_argument('--ids', nargs='+')
    p.add_argument('--allow-reviewed', action='store_true')
    p.add_argument('--limit', type=int)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    raw = args.ledger.read_bytes()
    reviews = json.loads(args.reconciliation.read_bytes())
    if hashlib.sha256(raw).hexdigest() != reviews['source']['ledger_sha256']:
        raise ValueError('Ledger bytes do not match the reconciliation source pin')
    ledger = json.loads(raw)
    rows = select(ledger, reviews, args.ids, args.allow_reviewed)
    if args.limit is not None:
        if args.limit < 1:
            raise ValueError('--limit must be positive')
        rows = rows[:args.limit]
    result = {'source_entries': len(ledger['entries']),
              'awaiting_initial_review': len(ledger['entries']) - len(reviews['entries']),
              'selected_initial_reviews': sum(r['work_type'] == 'initial review' for r in rows),
              'selected_followups': sum(r['work_type'] == 'follow-up' for r in rows),
              'interpretation': 'Reviewed does not mean completed or excluded. Entries can overlap and contain several subclaims.',
              'entries': rows}
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(text, encoding='utf-8', newline='\n')
    else:
        # Preserve source claims when Windows pipes default to a legacy encoding.
        sys.stdout.reconfigure(encoding='utf-8')
        print(text, end='')


if __name__ == '__main__':
    main()
