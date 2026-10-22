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


def validate_plan_provenance(root, identifier, reproduction):
    """Check conventional JSON plan/report links without executing experiment code."""
    plan_path = f'experiments/records/{identifier}/plan.json'
    declared_inputs = {entry['path']: entry for entry in reproduction['inputs']}
    if not (root / plan_path).is_file():
        return
    require(plan_path in declared_inputs, 'Plan must be a declared hashed input: ' + plan_path)
    plan_bytes = local(root, plan_path).read_bytes()
    plan = json.loads(plan_bytes)
    require(isinstance(plan, dict), 'Plan must be a JSON object: ' + plan_path)
    dependencies = plan.get('inputs', [])
    require(isinstance(dependencies, list), 'Plan inputs must be a list: ' + plan_path)
    for dependency in dependencies:
        require(isinstance(dependency, dict), 'Invalid plan dependency: ' + plan_path)
        name = dependency.get('path')
        data = local(root, name).read_bytes()
        require(name in declared_inputs, 'Plan dependency must be a declared input: ' + name)
        require(hashlib.sha256(data).hexdigest() == dependency.get('sha256'),
                'Plan input SHA-256 mismatch: ' + plan_path + ' -> ' + name)
    results_path = f'experiments/records/{identifier}/results.json'
    if results_path in {entry['path'] for entry in reproduction['outputs']}:
        results = json.loads(local(root, results_path).read_bytes())
        if isinstance(results, dict) and 'plan_sha256' in results:
            require(results['plan_sha256'] == hashlib.sha256(plan_bytes).hexdigest(),
                    'Saved report plan SHA-256 mismatch: ' + results_path)


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
        require(isinstance(scope.get('pages'), list)
                and all(x in pages for x in scope['pages']), 'Scope needs valid page IDs')
        artifacts = scope.get('artifacts', [])
        require(isinstance(artifacts, list) and all(isinstance(x, str) for x in artifacts),
                'Scope artifacts must be a list of local input paths')
        require(scope['pages'] or artifacts, 'Scope needs pages or source artifacts')
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
        validate_plan_provenance(root, identifier, reproduction)
        require(all(a in [f['path'] for f in reproduction['inputs']] for a in artifacts),
                'Scope artifacts must be declared hashed inputs')
        for visual in d.get('visuals', []):
            text(visual.get('caption'), 'visual caption')
            require(visual.get('path') in [f['path'] for f in reproduction['outputs']]
                    and re.fullmatch(r'[a-zA-Z0-9_./-]+\.(svg|png|jpg|webp)', visual['path']),
                    'Visual must be a declared image output')
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
    # Editorial record types travel with complete evidence, including offline exports.
    type_path = root / 'data/method-families.json'
    if type_path.exists():
        types = json.loads(type_path.read_text(encoding='utf-8'))
        assignments = types['record_kind_by_id']
        require(set(assignments) == ids, 'Record types must cover exactly the published records')
        for record in records:
            kind_id = assignments[record['id']]
            definition = types['record_kinds'][kind_id]
            text(definition.get('label'), 'record type label')
            text(definition.get('description'), 'record type description')
            record['record_type'] = {'id': kind_id, **definition}
    for d in records:
        require(all(x in ids and x != d['id'] for x in d['related']),
                'Related IDs must name other published records')
    by_id = {r['id']: r for r in records}
    for r in records:
        family = r.get('family')
        if family is None:  # Older independent records remain readable.
            continue
        require(isinstance(family, dict), 'Invalid experiment family')
        for key in ('id', 'title', 'question', 'baseline'):
            text(family.get(key), 'family.' + key)
        require(re.fullmatch(r'[a-z][a-z0-9-]*', family['id']), 'Invalid family ID')
        baseline = by_id.get(family['baseline'])
        require(baseline and baseline.get('family') == family,
                'Family baseline must be published with identical family metadata')
        variant = r.get('variant', {})
        text(variant.get('label'), 'variant.label')
        changes = variant.get('changes')
        require(isinstance(changes, list), 'List variant changes')
        expected = {k for k in baseline['scope'] if baseline['scope'][k] != r['scope'][k]}
        require(len(changes) == len(expected), 'List every scope difference exactly once')
        seen = set()
        for change in changes:
            field = change.get('field')
            require(field in expected and field not in seen, 'Invalid or duplicate changed field')
            seen.add(field)
            require(change.get('before') == baseline['scope'][field] and
                    change.get('after') == r['scope'][field], 'Variant comparison must match recorded scope')
            text(change.get('reason'), 'Reason for variant')
        require(r['id'] == family['baseline'] or expected,
                'A variant needs a scope change; document an identical retest in the original record')
    families = {}
    for r in records:
        if r.get('family'):
            f = r['family']
            require(f['id'] not in families or families[f['id']] == f,
                    'Conflicting family metadata')
            families[f['id']] = f
    (root / 'data/experiments.json').write_text(json.dumps({
        'schema': 'liberpedia-experiments-v1', 'records': records
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    # Discovery stays small; a selected record retains its complete scope and evidence.
    base = 'https://jelliottdev.github.io/'
    export_dir = root / 'reference/experiments'
    export_dir.mkdir(parents=True, exist_ok=True)
    require(export_dir.resolve().is_relative_to(root.resolve()), 'Export directory escapes repository')
    published_ids = {record['id'] for record in records}
    for previous in export_dir.glob('*.json'):
        require(previous.resolve().is_relative_to(export_dir.resolve()), 'Export path escapes directory')
        if previous.stem not in published_ids:
            previous.unlink()
    discovery = []
    for record in records:
        identifier = record['id']
        path = f'reference/experiments/{identifier}.json'
        (root / path).write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n',
                                encoding='utf-8', newline='\n')
        discovery.append({
            'id': identifier, 'title': record['title'], 'question': record['question'],
            'summary': record['summary'], 'tags': record['tags'],
            'family': record.get('family'), 'variant_label': record.get('variant', {}).get('label'),
            'pages': record['scope']['pages'], 'artifacts': record['scope'].get('artifacts', []),
            'outcome': record['outcome'], 'retested_on': record['review']['retested_on'],
            'url': base + '#/experiments/' + identifier, 'record_url': base + path,
            'article_url': base + record['article_path'],
            'bundle_url': base + 'downloads/experiments/' + identifier + '.zip',
        })
    (root / 'data/experiment-index.json').write_text(json.dumps({
        'schema': 'liberpedia-experiment-discovery-v1',
        'usage': 'Discovery only. Fetch record_url and compare the complete scope, findings, '
                 'limitations and review before claiming an idea was tested. No match means '
                 'no matching documented record here, not proof that an idea is new.',
        'records': discovery,
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
