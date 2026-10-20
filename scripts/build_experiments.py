"""Validate reviewed records and build the public experiment index. No scripts are executed."""
import datetime
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(value, message):
    if not value:
        raise ValueError(message)


def text(value, label):
    require(isinstance(value, str) and value.strip(), f'{label}: expected nonempty text')


def local(root, path):
    require(isinstance(path, str) and path and '\\' not in path and not Path(path).is_absolute(),
            f'Invalid relative path: {path}')
    file = (root / path).resolve()
    require(file.is_relative_to(root.resolve()), f'Path escapes repository: {path}')
    require(file.is_file(), f'Missing file: {path}')
    return file


def build(root=ROOT):
    records = []
    pages = {p['id'] for p in json.loads((root / 'data/index.json').read_text(encoding='utf-8'))['pages']}
    for path in sorted((root / 'experiments/records').glob('*/record.json')):
        d = json.loads(path.read_text(encoding='utf-8'))
        require(d.get('status') in ('draft', 'published'), f'{path}: invalid status')
        if d['status'] == 'draft':
            continue
        identifier = d.get('id', '')
        require(re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', identifier)
                and path.parent.name == identifier, 'Invalid or mismatched ID')
        for key in ('title', 'question', 'summary', 'finding', 'limitations', 'next_steps'):
            text(d.get(key), f'{identifier}.{key}')
        require(d.get('outcome') in ('supported', 'not-supported', 'inconclusive'), 'Invalid outcome')
        scope = d.get('scope', {})
        require(isinstance(scope.get('pages'), list) and scope['pages']
                and all(x in pages for x in scope['pages']), 'Scope needs valid page IDs')
        for key in ('representation', 'procedure', 'parameters', 'exclusions'):
            text(scope.get(key), 'scope.' + key)
        for key in ('tags', 'related'):
            require(isinstance(d.get(key), list)
                    and all(isinstance(x, str) and x.strip() for x in d[key]), 'Invalid ' + key)
        review = d.get('review', {})
        text(review.get('reviewer'), 'review.reviewer')
        date = datetime.date.fromisoformat(review.get('retested_on', ''))
        require(date <= datetime.date.today(), 'Retest date is in the future')
        reproduction = d.get('reproduction', {})
        for key in ('command', 'environment', 'script'):
            text(reproduction.get(key), 'reproduction.' + key)
        require(reproduction['script'].startswith(f'experiments/records/{identifier}/'),
                'Script must live with its record')
        script = local(root, reproduction['script'])
        script_bytes = script.read_bytes()
        require(b'No experiment implemented.' not in script_bytes, 'Replace the draft script')
        script_digest = hashlib.sha256(script_bytes).hexdigest()
        require(script_digest == reproduction.get('script_sha256'),
                'Script SHA-256 mismatch: retest the script and record its reviewed hash')
        for role in ('inputs', 'outputs'):
            entries = reproduction.get(role)
            require(isinstance(entries, list) and entries, 'List exact ' + role)
            for file in entries:
                data = local(root, file.get('path')).read_bytes()
                require(hashlib.sha256(data).hexdigest() == file.get('sha256'),
                        'SHA-256 mismatch: ' + str(file.get('path')))
        require(isinstance(d.get('sources'), list) and d['sources'], 'Provide source references')
        for source in d['sources']:
            text(source.get('label'), 'source label')
            require(isinstance(source.get('url'), str) and source['url'].startswith('https://'),
                    'Source must use HTTPS')
        article = local(root, f'experiments/records/{identifier}/article.md').read_text(encoding='utf-8')
        require(len(article.strip()) >= 200 and 'State one testable question.' not in article,
                'Replace the article template with a full account')
        d['article'] = article
        d['article_path'] = f'experiments/records/{identifier}/article.md'
        d['script_sha256'] = script_digest
        records.append(d)
    ids = {d['id'] for d in records}
    for d in records:
        require(all(x in ids and x != d['id'] for x in d['related']),
                'Related IDs must name other published records')
    (root / 'data/experiments.json').write_text(json.dumps({
        'schema': 'liberpedia-experiments-v1', 'records': records
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    body = '<h1>Experiment records</h1>'
    if not records:
        body += '<p>No experiment records have been published yet.</p>'
    for d in records:
        body += '<article id="' + d['id'] + '"><pre style="white-space:pre-wrap;overflow-wrap:anywhere">'
        body += html.escape(json.dumps(d, ensure_ascii=False, indent=2)) + '</pre></article>'
    (root / 'reference/experiments.html').write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Experiments — Liberpedia</title><body>'
        '<a href="../index.html#/experiments">Have we tried it?</a><main>' + body + '</main></body></html>',
        encoding='utf-8', newline='\n')
    print(f'Published {len(records)} reviewed experiment records')
    return records


if __name__ == '__main__':
    build()
