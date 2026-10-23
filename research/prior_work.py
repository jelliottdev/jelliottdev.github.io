"""Internal intake lookup. Candidate matches are not evidence of completed coverage."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_bytes())


def ledger_path(path):
    # Ledger evidence is relative to liber-primus; callers also use repo paths.
    return path.removeprefix('liber-primus/')


def lookup(source_id=None, source_path=None, terms='', limit=12):
    inventory = read(ROOT / 'research/public-attempt-inventory.json')
    entries = inventory['entries']
    candidates = []
    resolution = 'not-requested'
    if source_id:
        key = source_id.strip().casefold()
        candidates = [r for r in entries if r['source_id'].casefold() == key]
        resolution = 'exact'
        if not candidates:
            candidates = [r for r in entries if r['source_id'].casefold().startswith(key + '-')]
            resolution = 'unique-prefix'
    elif source_path:
        candidates = [r for r in entries if any(
            url.endswith('/' + source_path) or url.endswith('/' + ledger_path(source_path))
            for url in r.get('source_evidence_urls', []))]
        resolution = 'source-path'
    if source_id or source_path:
        if not candidates:
            resolution = 'not-found'
        elif len(candidates) > 1:
            resolution = 'ambiguous'
    entry = candidates[0] if len(candidates) == 1 else None
    input_dependencies = []
    candidate_ids = {r['source_id'] for r in candidates}
    for note in sorted((ROOT / 'research').glob('*-input-dependency-*.json')):
        dependency = read(note)
        if dependency.get('schema') != 'internal-source-input-dependency-v1':
            continue
        applicable = [r for r in dependency['confirmed_dependent_source_ids']
                      if r['source_id'] in candidate_ids or
                      (source_path and ledger_path(r['source_path']) == ledger_path(source_path))]
        if applicable:
            input_dependencies.append({
                'note': note.relative_to(ROOT).as_posix(),
                'checked_on': dependency['checked_on'],
                'revision': dependency['revision'],
                'applies_to': applicable,
                'missing_inputs': dependency['missing_inputs'],
                'scope_note': dependency['effect'],
                'usage': 'Recorded input check, not a fresh probe. Recheck if source or recovered files change.',
            })
    execution_gates = []
    source_audits = []
    audit_path = ROOT / 'research/source-audit-register.json'
    if audit_path.exists():
        register = read(audit_path)
        if register.get('schema') == 'internal-source-audit-register-v1':
            source_audits = [row for row in register['entries']
                             if row['source_id'] in candidate_ids]
    resolved_ids = {identifier.casefold() for identifier in candidate_ids}
    if source_id:
        resolved_ids.add(source_id.strip().casefold())
    for note in sorted((ROOT / 'research').glob('*-execution-gate-*.json')):
        gate = read(note)
        if gate.get('schema') != 'internal-source-execution-gate-v1':
            continue
        paths = set(gate.get('source_paths', []))
        paths.update(item['path'] for item in gate.get('control_evidence', []))
        matches_id = gate.get('source_id', '').casefold() in resolved_ids
        matches_path = bool(source_path and any(
            ledger_path(path) == ledger_path(source_path) for path in paths))
        if matches_id or matches_path:
            execution_gates.append({
                'note': note.relative_to(ROOT).as_posix(),
                'evidence': gate,
                'usage': 'Recorded source-gate check, not a fresh probe or cipher exclusion. '
                         'Recheck if source, inputs or control rule changes.',
            })
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
            'source_lookup': resolution,
            'source_candidates': [{'source_id': r['source_id'], 'source_lane': r.get('source_lane'),
                                   'reconciliation_state': r.get('reconciliation_state')}
                                  for r in candidates] if len(candidates) > 1 else [],
            'source_entry': entry, 'input_dependencies': input_dependencies,
            'execution_gates': execution_gates, 'source_audits': source_audits,
            'matches': hits[:limit]}


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
