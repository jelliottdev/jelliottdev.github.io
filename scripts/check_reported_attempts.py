"""Check reported-attempt intake without treating it as experiment evidence."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
register = json.loads((ROOT / 'data/reported-attempts.json').read_text(encoding='utf-8'))
entries = register['entries']
assert register['schema'] == 'liberpedia-reported-attempts-v1'
assert len(entries) == len({entry['id'] for entry in entries})
families = {row['id'] for row in json.loads((ROOT / 'data/method-families.json').read_text(encoding='utf-8'))['families']}
experiments = {row['id'] for row in json.loads((ROOT / 'data/experiments.json').read_text(encoding='utf-8'))['records']}
article = (ROOT / 'articles/reported-attempts.html').read_text(encoding='utf-8')
local_sources_checked = 0
for entry in entries:
    assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', entry['id'])
    assert entry['phrases'] and all(isinstance(phrase, str) and phrase.strip() for phrase in entry['phrases'])
    assert len(entry['phrases']) == len({phrase.casefold().strip() for phrase in entry['phrases']})
    assert entry['status'] in {'not-replayed', 'related-only', 'partial'}
    assert entry['family'] in families
    assert all(record in experiments for record in entry['related_records'])
    assert all(re.fullmatch(r'lp[12]-\d{2}', page) for page in entry['pages'])
    assert all(entry[field].strip() for field in ('title', 'reported_idea', 'coverage', 'replay_needed'))
    source = entry['source']
    assert all(source[field].strip() for field in ('title', 'author', 'reported', 'attachment_id', 'sha256'))
    assert re.fullmatch(r'[0-9a-f]{64}', source['sha256'])
    assert source.get('public_url', 'https://example.invalid').startswith('https://')
    assert article.count(f'<section id="{entry["id"]}">') == 1
    local = Path.home() / '.codex' / 'attachments' / source['attachment_id'] / 'Pasted text.txt'
    if local.exists():
        assert hashlib.sha256(local.read_bytes()).hexdigest() == source['sha256'], local
        local_sources_checked += 1
assert article.count('<section id=') == len(entries)
print(f'PASS: {len(entries)} distinct reported attempts, valid family/record links and {local_sources_checked} available source hashes.')
