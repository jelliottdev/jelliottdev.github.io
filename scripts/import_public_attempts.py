"""Index a pinned public research ledger without adopting its conclusions."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'f08b20b632d91209ddbaa747e8e2f23df0c78ba1'
EXPECTED_SHA = '7718bf90fb4cc6cc0fb98464d65ab898dd0e776da33d9b056bcd908d3b60558d'
BASE = f'https://github.com/Dukotah/cicada3301/blob/{REVISION}/'


def source_path(url):
    parsed = urlsplit(url)
    if parsed.hostname not in ('github.com', 'raw.githubusercontent.com'):
        return None
    path = unquote(parsed.path)
    for prefix in ('/Dukotah/cicada3301/blob/', '/Dukotah/cicada3301/'):
        if path.startswith(prefix):
            remainder = path[len(prefix):].split('/', 1)
            if len(remainder) == 2:
                return remainder[1]
    return None


def build(root, ledger_bytes):
    if hashlib.sha256(ledger_bytes).hexdigest() != EXPECTED_SHA:
        raise ValueError('Use the exact pinned ledger; source hash differs')
    source = json.loads(ledger_bytes)
    references = []
    registry_bytes = (root / 'data/experiments.json').read_bytes()
    registry = json.loads(registry_bytes)
    record_ids = {record['id'] for record in registry['records']}
    review_path = root / 'research/public-attempt-reconciliation.json'
    reviews = {}
    if review_path.is_file():
        review_data = json.loads(review_path.read_bytes())
        if review_data['source']['ledger_sha256'] != EXPECTED_SHA:
            raise ValueError('Reconciliation uses a different source ledger')
        reviews = {row['source_id']: row for row in review_data['entries']}
    for record in registry['records']:
        article = record.get('article', '')
        urls = [item['url'] for item in record.get('sources', [])]
        urls += re.findall(r'https://[^\s)<>"\]]+', article)
        paths = {path for url in urls if (path := source_path(url))}
        references.append((record['id'], json.dumps(record, ensure_ascii=False) + '\n' + article, paths))
    rows, command_groups, evidence_groups = [], defaultdict(list), defaultdict(list)
    for entry in source['entries']:
        identifier = entry['id']
        evidence = [path for path in entry.get('evidence', []) if isinstance(path, str)]
        command = entry.get('reproduce') or ''
        script_paths = set(re.findall(r'liber-primus/[^\s;"\']+\.py', command))
        candidates = []
        for record_id, text, paths in references:
            reasons = []
            overlap = sorted(paths & (set(evidence) | script_paths))
            if overlap:
                reasons.append({'kind': 'shared_source_file', 'paths': overlap})
            if len(identifier) >= 6 and re.search(r'(?<![A-Za-z0-9-])' + re.escape(identifier) + r'(?![A-Za-z0-9-])', text):
                reasons.append({'kind': 'explicit_source_entry_id'})
            if reasons:
                candidates.append({'record_id': record_id, 'reasons': reasons})
        rows.append({
            'source_id': identifier, 'source_hypothesis': entry.get('hypothesis', ''),
            'source_status': entry.get('status'), 'source_lane': entry.get('lane'),
            'source_reproduction_command': command or None,
            'source_evidence_urls': [BASE + path for path in evidence],
            'source_supersedes': entry.get('supersedes') or [],
            'source_superseded_by': entry.get('superseded_by'),
            'reconciliation_state': 'candidate-overlap' if candidates else 'unreconciled',
            'candidate_records': candidates,
            'coverage_verified': False,
        })
        if identifier in reviews:
            review = reviews[identifier]
            rejected = {item['record_id'] for item in review.get('rejected_inventory_candidates', [])}
            rows[-1]['candidate_records'] = [item for item in candidates if item['record_id'] not in rejected]
            rows[-1]['reconciliation_state'] = review['status']
            rows[-1]['reviewed_subclaims'] = {
                'record_links': [item for item in review.get('record_links', []) if item['record_id'] in record_ids],
                'unresolved_parts': review.get('unresolved_parts', []),
                'rejected_candidates': review.get('rejected_inventory_candidates', []),
                'audit_note': review.get('audit_note'),
            }
            # Full coverage is a separate, explicit claim; none is inferred from a link.
            rows[-1]['coverage_verified'] = review.get('whole_entry_coverage_verified') is True
        if command:
            command_groups[command].append(identifier)
        if evidence:
            evidence_groups[tuple(sorted(evidence))].append(identifier)
    statuses = dict(sorted(Counter(row['source_status'] for row in rows).items()))
    overlap_count = sum(bool(row['candidate_records']) for row in rows)
    reviewed_count = sum('reviewed_subclaims' in row for row in rows)
    return {
        'schema': 'liberpedia-public-attempt-inventory-v1',
        'source': {'repository': 'Dukotah/cicada3301', 'revision': REVISION,
                   'url': BASE + 'liber-primus/LEDGER.json', 'sha256': EXPECTED_SHA,
                   'license_url': BASE + 'LICENSE'},
        'registry_snapshot': {'path': 'data/experiments.json', 'sha256': hashlib.sha256(registry_bytes).hexdigest(),
                              'record_count': len(registry['records'])},
        'usage': 'Internal source reconciliation. Entries are research units, not deduplicated solving ideas. '
                 'Source status labels are unverified claims. Candidate links locate related source material; '
                 'they do not prove a replay or complete coverage. Compare rules, inputs and bounds before changing coverage_verified.',
        'counts': {'source_entries': len(rows), 'source_statuses': statuses,
                   'with_reproduction_command': sum(bool(row['source_reproduction_command']) for row in rows),
                   'candidate_overlap': overlap_count,
                   'unreconciled': sum(row['reconciliation_state'] == 'unreconciled' for row in rows),
                   'source_entries_reviewed': reviewed_count,
                   'verified_coverage': sum(row['coverage_verified'] for row in rows)},
        'triage_groups': {
            'shared_reproduction_command': [{'source_ids': ids, 'command': command}
                                            for command, ids in command_groups.items() if len(ids) > 1],
            'shared_evidence_files': [{'source_ids': ids, 'urls': [BASE + path for path in files]}
                                      for files, ids in evidence_groups.items() if len(ids) > 1],
        },
        'entries': rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ledger', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'research/public-attempt-inventory.json')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = build(ROOT, args.ledger.read_bytes())
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.check:
        assert args.output.read_text(encoding='utf-8') == encoded
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding='utf-8', newline='\n')
    print(json.dumps(result['counts']))


if __name__ == '__main__':
    main()
