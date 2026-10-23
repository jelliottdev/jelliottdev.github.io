"""Internal intake lookup. Candidate matches are not evidence of completed coverage."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_bytes())


def lookup(source_id=None, source_path=None, terms='', limit=12):
    inventory = read(ROOT / 'research/public-attempt-inventory.json')
    entry = next((r for r in inventory['entries'] if r['source_id'] == source_id), None)
    linked = set()
    if entry:
        linked.update(x['record_id'] for x in entry.get('candidate_records', []))
        linked.update(x['record_id'] for x in entry.get('reviewed_subclaims', {}).get('record_links', []))
    words = set(re.findall(r'[a-z0-9]{3,}', terms.lower()))
    hits = []
    for path in sorted((ROOT / 'experiments/records').glob('*/record.json')):
        record = read(path)
        if record.get('status') not in ('published', 'draft'):
            continue
        article = path.parent / 'article.md'
        body = article.read_text(encoding='utf-8') if article.exists() else ''
        fields = [(record.get('title', ''), 6), (record.get('question', ''), 4),
                  (' '.join(record.get('tags', [])), 4),
                  (json.dumps(record, ensure_ascii=False) + body, 1)]
        score = sum(weight * len(words & set(re.findall(r'[a-z0-9]{3,}', text.lower())))
                    for text, weight in fields)
        reasons = []
        if record['id'] in linked:
            score += 200
            reasons.append('source inventory already links this record')
        if source_path and source_path in fields[-1][0]:
            score += 200
            reasons.append('exact source path cited')
        if score:
            hits.append({'record_id': record['id'], 'status': record['status'],
                         'title': record['title'], 'score': score,
                         'reasons': reasons or ['word overlap; inspect the actual scope'],
                         'path': path.relative_to(ROOT).as_posix()})
    hits.sort(key=lambda r: (-r['score'], r['record_id']))
    return {'warning': 'Intake candidates only. Read scope, gates and unresolved parts before assigning work.',
            'source_entry': entry, 'matches': hits[:limit]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-id')
    parser.add_argument('--source-path')
    parser.add_argument('--terms', default='')
    parser.add_argument('--limit', type=int, default=12)
    args = parser.parse_args()
    if not (args.source_id or args.source_path or args.terms):
        parser.error('Provide a source ID, source path or terms.')
    print(json.dumps(lookup(args.source_id, args.source_path, args.terms, args.limit),
                     ensure_ascii=True, indent=2))
