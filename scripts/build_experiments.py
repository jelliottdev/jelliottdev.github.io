"""Validate published record files and build the public index. No scripts are executed."""
import datetime
import hashlib
import html
import json
import re
from pathlib import Path
from experiment_content import compile_content, article_bytes

ROOT = Path(__file__).resolve().parents[1]

# Preserve exact evidence and lexical text; detail/download dependencies stay separate.
CHECKER_FIELDS = ('id', 'status', 'title', 'question', 'summary', 'tags', 'record_type',
                  'family', 'variant', 'scope', 'outcome', 'finding', 'limitations',
                  'article', 'method_topics', 'reader_finding', 'reader_limit', 'materials', 'discovery',
                  'recorded_comparison')


def checker_payload(records, registry_bytes):
    return {
        'schema': 'liberpedia-checker-records-v1',
        'registry_sha256': hashlib.sha256(registry_bytes).hexdigest(),
        'records': [{key: record[key] for key in CHECKER_FIELDS if key in record}
                    for record in records],
    }


def require(value, message):
    if not value:
        raise ValueError(message)


def text(value, label):
    require(isinstance(value, str) and value.strip(), f'{label}: expected nonempty text')


def validate_reader_sections(markdown, titles):
    """Selected visible H2 sections must be exact and unambiguous outside fences."""
    require(isinstance(titles, list) and len(titles) <= 3
            and all(isinstance(title, str) and title.strip()
                    and not re.search(r'[\r\n]', title) for title in titles),
            'reader_sections: expected up to three nonempty H2 titles')
    require(len(set(titles)) == len(titles), 'reader_sections: duplicate titles')
    headings = []
    fence = None
    for line in markdown.split('\n'):
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if (marker and marker[1][0] == fence[0]
                    and len(marker[1]) >= len(fence) and not marker[2].strip()):
                fence = None
            continue
        if marker:
            fence = marker[1]
            continue
        heading = re.match(r'^ {0,3}##[\t ]+(.+?)\r?$', line)
        if heading:
            headings.append(heading[1])
    for title in titles:
        require(headings.count(title) == 1,
                'reader_sections must name exactly one authored H2: ' + title)


def validate_discovery(discovery):
    """Authored candidate-search hints, never an assertion of exact coverage."""
    require(isinstance(discovery, dict) and set(discovery) == {'operations', 'evaluation'},
            'discovery: expected operations and evaluation only')
    operations = discovery['operations']
    require(isinstance(operations, list) and 1 <= len(operations) <= 8,
            'discovery.operations: expected 1..8 unique operations')
    seen = set()
    for operation in operations:
        require(isinstance(operation, dict) and set(operation) == {'action', 'operand', 'within'},
                'discovery operation: unexpected fields')
        require(operation['action'] == 'reverse'
                and operation['operand'] in ('rune-order', 'word-order')
                and operation['within'] in ('row', 'word', 'page'),
                'discovery operation: invalid controlled value')
        signature = tuple(operation[key] for key in ('action', 'operand', 'within'))
        require(signature not in seen, 'discovery.operations: duplicate operation')
        seen.add(signature)
    evaluation = discovery['evaluation']
    require(isinstance(evaluation, list) and 1 <= len(evaluation) <= 4
            and all(value in ('known-opening', 'english-readability') for value in evaluation)
            and len(set(evaluation)) == len(evaluation),
            'discovery.evaluation: expected unique controlled evaluations')


def validate_recorded_comparison(value, scope, pages):
    """Match recorded-comparison.js reviewed metadata; no coverage inference."""
    require(isinstance(value, dict) and set(value) == {
        'version', 'operation', 'executed_pages', 'evaluation', 'input_description', 'reuse'},
        'recorded_comparison: unexpected fields')
    require(type(value['version']) in (int, float) and value['version'] == 1,
            'recorded_comparison.version: expected 1')
    operation = value['operation']
    require(isinstance(operation, dict) and set(operation) == {'action', 'operand', 'within'}
            and operation == {'action': 'reverse', 'operand': 'rune-order', 'within': 'row'},
            'recorded_comparison.operation: unsupported signature')

    def canonical(values):
        return (isinstance(values, list) and 1 <= len(values) <= 75
                and all(isinstance(page, str) and re.fullmatch(r'lp[12]-[0-9]{2}', page)
                        and int(page[4:]) <= (16 if page.startswith('lp1') else 57)
                        and page in pages for page in values)
                and values == sorted(set(values)))

    executed = value['executed_pages']
    declared = scope.get('pages') if isinstance(scope, dict) else None
    require(canonical(executed) and canonical(declared)
            and set(executed) <= set(declared),
            'recorded_comparison.executed_pages: expected canonical nonempty subset of scope')
    evaluation = value['evaluation']
    require(isinstance(evaluation, dict) and set(evaluation) == {'kind', 'description', 'limitation'}
            and evaluation['kind'] in ('known-opening', 'english-score'),
            'recorded_comparison.evaluation: unsupported fields or kind')
    # ECMAScript trim whitespace and UTF-16 length, including astral characters.
    whitespace = '\u0009\u000a\u000b\u000c\u000d\u0020\u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000\ufeff'
    for name, prose in (('input_description', value['input_description']), ('reuse', value['reuse']),
                        ('evaluation.description', evaluation['description']),
                        ('evaluation.limitation', evaluation['limitation'])):
        require(isinstance(prose, str) and prose == prose.strip(whitespace)
                and 0 < len(prose.encode('utf-16-le', errors='surrogatepass')) // 2 <= 500
                and not re.search(r'[\x00-\x1f\x7f\[\]`*\\]', prose),
                'recorded_comparison.' + name + ': expected bounded plain prose')


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


def validate_batch(root, record):
    """Validate a lazy case attachment without inflating the experiment count."""
    batch = record.get('batch')
    if batch is None:
        return
    require(isinstance(batch, dict), 'Batch metadata must be an object')
    for key in ('suite_id', 'manifest_path', 'cases_path', 'scope_note'):
        text(batch.get(key), 'batch.' + key)
    inputs = {item['path'] for item in record['reproduction']['inputs']}
    outputs = {item['path'] for item in record['reproduction']['outputs']}
    require(batch['manifest_path'] in inputs, 'Suite manifest must be a declared hashed input')
    require(batch['cases_path'] in outputs, 'Suite cases must be a declared hashed output')
    manifest = json.loads(local(root, batch['manifest_path']).read_bytes())
    attachment = json.loads(local(root, batch['cases_path']).read_bytes())
    require(manifest.get('suite_id') == attachment.get('suite_id') == batch['suite_id'],
            'Suite IDs must match record, manifest and case attachment')
    require(attachment.get('schema') == 'liberpedia-feedback-opening-cases-v1',
            'Unregistered case schema')
    cases = attachment.get('cases')
    require(isinstance(cases, list) and cases and type(batch.get('case_count')) is int
            and len(cases) == batch['case_count'], 'Suite case count mismatch')
    ids = [case.get('id') for case in cases]
    require(all(isinstance(identifier, str) and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', identifier)
                for identifier in ids) and len(set(ids)) == len(ids), 'Invalid or duplicate suite case ID')
    crib_length = max((len(crib.get('indices', [])) for crib in manifest.get('cribs', [])), default=12)
    for case in cases:
        require(case.get('mode') in ('ciphertext', 'plaintext')
                and case.get('boundary') in ('continuous', 'word-reset'), 'Invalid feedback rule')
        require(type(case.get('lag')) is int and 1 <= case['lag']
                and type(case.get('primer')) is int and 0 <= case['primer'] < 29,
                'Invalid feedback parameters')
        require(type(case.get('comparison_count')) is int and case['comparison_count'] >= 0,
                'Invalid case comparison count')
        require(isinstance(case.get('opening_matches'), list)
                and type(case.get('max_prefix_length')) is int and 0 <= case['max_prefix_length'] <= crib_length,
                'Invalid case finding')
        require(isinstance(case.get('decode_sha256'), str)
                and re.fullmatch(r'[0-9a-f]{64}', case['decode_sha256']), 'Invalid decoded-output hash')


def validate_record(root, path, pages):
    """Validate one completed record without publishing it or executing its scripts."""
    raw = json.loads(path.read_text(encoding='utf-8'))
    d = compile_content(raw)
    generated_article = article_bytes(raw)
    if 'discovery' in d:
        validate_discovery(d['discovery'])
    require(d.get('status') in ('draft', 'published'), f'{path}: invalid status')
    identifier = d.get('id', '')
    require(re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', identifier)
            and path.parent.name == identifier, 'Invalid or mismatched ID')
    for key in ('title', 'question', 'summary', 'finding', 'limitations', 'next_steps'):
        text(d.get(key), f'{identifier}.{key}')
    require(d.get('outcome') in ('supported', 'not-supported', 'inconclusive'), 'Invalid outcome')
    scope = d.get('scope', {})
    require(isinstance(scope.get('pages'), list)
            and all(x in pages for x in scope['pages']), 'Scope needs valid page IDs')
    if 'recorded_comparison' in d:
        validate_recorded_comparison(d['recorded_comparison'], scope, pages)
    if 'pages_note' in d:
        text(d['pages_note'], f'{identifier}.pages_note')
    if 'bounds_note' in d:
        text(d['bounds_note'], f'{identifier}.bounds_note')
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
    text(review.get('kind'), 'review.kind')
    require(review.get('human_review') in ('pending', 'complete'),
            f'{identifier}: human review must be explicitly pending or complete')
    if review['human_review'] == 'complete':
        text(review.get('human_reviewer'), 'review.human_reviewer')
        text(review.get('human_findings'), 'review.human_findings')
        human_date = datetime.date.fromisoformat(review.get('human_reviewed_on', ''))
        require(human_date <= datetime.date.today(), 'Human review date is in the future')
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
            name = file.get('path', '')
            require('__pycache__' not in name.split('/') and not name.endswith(('.pyc', '.pyo')),
                    'Declare source files, not generated Python caches: ' + name)
            data = (generated_article if generated_article is not None and file.get('path') == f'experiments/records/{identifier}/article.md'
                    else local(root, file.get('path')).read_bytes())
            require(hashlib.sha256(data).hexdigest() == file.get('sha256'),
                    'SHA-256 mismatch: ' + str(file.get('path')))
    command_files = set(re.findall(r'(?:experiments/records|scripts)/[\w./-]+\.py',
                                  reproduction['command']))
    bundled_files = {reproduction['script'],
                     *(f['path'] for f in reproduction['inputs']),
                     *(f['path'] for f in reproduction['outputs'])}
    require(command_files <= bundled_files,
            'Reproduction command uses undeclared bundle files: ' +
            ', '.join(sorted(command_files - bundled_files)))
    if 'materials' in d:
        materials = d['materials']
        require(isinstance(materials, dict) and set(materials) == {'summary', 'reuse', 'limits', 'evidence'},
                'Materials needs summary, reuse, limits and evidence')
        for key in ('summary', 'reuse', 'limits'):
            text(materials.get(key), 'materials.' + key)
        evidence = materials.get('evidence')
        require(isinstance(evidence, list) and 1 <= len(evidence) <= 3
                and all(isinstance(name, str) and name in bundled_files for name in evidence)
                and len(set(evidence)) == len(evidence),
                'Materials evidence must name 1–3 distinct declared reproduction files')
        require(len(json.dumps(materials, ensure_ascii=False, separators=(',', ':'))) <= 1200,
                'Materials exceeds the 1200-character evidence budget; shorten the complete note')
    validate_plan_provenance(root, identifier, reproduction)
    validate_batch(root, d)
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
    article = (generated_article.decode('utf-8') if generated_article is not None
               else local(root, f'experiments/records/{identifier}/article.md').read_text(encoding='utf-8'))
    if 'reader_sections' in d:
        validate_reader_sections(article, d['reader_sections'])
    require(len(article.strip()) >= 200 and 'State one testable question.' not in article,
            'Replace the article template with a full account')
    d['article'] = article
    d['article_path'] = f'experiments/records/{identifier}/article.md'
    d['script_sha256'] = script_digest
    return d


def validate_family(r, by_id):
    """Check a record's declared scope differences against its baseline."""
    family = r.get('family')
    if family is None:  # Older independent records remain readable.
        return
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


def authored_link_targets(markdown):
    """Match authored hyperlinks, excluding the renderer's fenced/inline code and images."""
    fenced = False
    for line in markdown.splitlines():
        if line.startswith('```'):
            fenced = not fenced
            continue
        if not fenced:
            prose = re.sub(r'`[^`]+`', '', line)
            yield from re.findall(r'(?<!!)\[[^\]\n]+\]\(([^)]+)\)', prose)


def article_link_aliases(root, record, published_ids):
    """Vetted navigation links, separate from hashed scientific/image dependencies."""
    aliases = {}
    declared = {record['article_path'], record['reproduction']['script']}
    declared.update(item['path'] for group in ('inputs', 'outputs')
                    for item in record['reproduction'][group])
    for href in authored_link_targets(record['article']):
        require(not re.match(r'^#/pages/lp[12]-\d{2}(?:[/?#]|$)', href, re.I),
                'Article page detail must use #/page/ or #/reader/, not #/pages/: '
                + record['id'] + ': ' + href)
        if href in declared or href.startswith(('https://', '#/')):
            continue
        # Unsafe examples stay escaped. Never decode or guess URL/path syntax.
        if not re.fullmatch(r'[a-zA-Z0-9_./-]+', href) or any(
                part in ('', '.', '..') for part in href.split('/')):
            continue
        zip_match = re.fullmatch(r'downloads/experiments/([a-z0-9-]+)\.zip', href)
        if zip_match:
            require(zip_match[1] in published_ids, 'Article ZIP must name a published record: ' + href)
            aliases[href] = href  # Bundles are built after this registry.
            continue
        candidate = root / href
        if '/' not in href or not candidate.is_file():
            candidate = root / Path(record['article_path']).parent / href
        resolved = candidate.resolve()
        known_account = re.fullmatch(r'experiments/records/([a-z0-9-]+)/article\.md', resolved.relative_to(root.resolve()).as_posix()) if resolved.is_relative_to(root.resolve()) else None
        require(resolved.is_relative_to(root.resolve()) and (resolved.is_file() or (known_account and known_account[1] in published_ids)),
                'Article link has no in-repository file: ' + record['id'] + ': ' + href)
        target = resolved.relative_to(root.resolve()).as_posix()
        owner = re.match(r'^experiments/records/([a-z0-9-]+)/', target)
        if owner:
            require(owner[1] in published_ids, 'Article link must name a published record: ' + target)
            if target == f'experiments/records/{owner[1]}/article.md':
                target = '#/experiments/' + owner[1]
        aliases[href] = target
    return aliases


def build(root=ROOT):
    records = []
    pages = {p['id'] for p in json.loads((root / 'data/index.json').read_text(encoding='utf-8'))['pages']}
    for path in sorted((root / 'experiments/records').glob('*/record.json')):
        d = json.loads(path.read_text(encoding='utf-8'))
        require(d.get('status') in ('draft', 'published'), f'{path}: invalid status')
        if d['status'] == 'draft':
            continue
        records.append(validate_record(root, path, pages))
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
            # Non-exclusive discovery hints from the authored method map. These
            # do not say that every variant of a family was tried.
            record['method_topics'] = [
                {'id': family['id'], 'title': family['title'], 'aliases': family['aliases']}
                for family in types['families'] if record['id'] in family['related']
            ]
    for d in records:
        require(all(x in ids and x != d['id'] for x in d['related']),
                'Related IDs must name other published records')
    by_id = {r['id']: r for r in records}
    for r in records:
        validate_family(r, by_id)
        r.pop('article_links', None)  # Export-only permissions are always derived here.
        aliases = article_link_aliases(root, r, ids)
        if aliases:
            r['article_links'] = aliases
    families = {}
    for r in records:
        if r.get('family'):
            f = r['family']
            require(f['id'] not in families or families[f['id']] == f,
                    'Conflicting family metadata')
            families[f['id']] = f
    # All records and relationships passed validation. Materialize compatibility
    # accounts only now; preflight/validate_record remain strictly read-only.
    for record in records:
        source = root / f"experiments/records/{record['id']}/record.json"
        account = article_bytes(json.loads(source.read_text(encoding='utf-8')))
        if account is not None:
            destination = root / record['article_path']
            require(destination.resolve().is_relative_to(root.resolve()), 'Generated account escapes repository')
            if not destination.exists() or destination.read_bytes() != account:
                destination.write_bytes(account)
    registry_text = json.dumps({'schema': 'liberpedia-experiments-v1', 'records': records},
                               ensure_ascii=False, indent=2) + '\n'
    (root / 'data/experiments.json').write_text(registry_text, encoding='utf-8', newline='\n')
    (root / 'data/checker-records.json').write_text(
        json.dumps(checker_payload(records, registry_text.encode('utf-8')),
                   ensure_ascii=False, separators=(',', ':')) + '\n',
        encoding='utf-8', newline='\n')
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
            'finding': record.get('reader_finding') or record['finding'],
            'scope': record['scope'], 'limitations': record['limitations'],
            'record_type': record.get('record_type'),
            'method_topics': record.get('method_topics', []),
            'family': record.get('family'), 'variant_label': record.get('variant', {}).get('label'),
            'pages': record['scope']['pages'], 'artifacts': record['scope'].get('artifacts', []),
            'outcome': record['outcome'], 'retested_on': record['review']['retested_on'],
            'url': base + '#/experiments/' + identifier, 'record_url': base + path,
            'article_url': base + record['article_path'],
            'bundle_url': base + 'downloads/experiments/' + identifier + '.zip',
        })
        if record.get('batch'):
            batch = record['batch']
            discovery[-1]['batch'] = {
                'suite_id': batch['suite_id'], 'case_count': batch['case_count'],
                'cases_url': base + batch['cases_path'],
                'manifest_url': base + batch['manifest_path'],
                'scope_note': batch['scope_note'],
            }
    (root / 'data/experiment-index.json').write_text(json.dumps({
        'schema': 'liberpedia-experiment-discovery-v1',
        'usage': 'Discovery only. Fetch record_url and compare the complete scope, findings, '
                 'limitations and review before claiming an idea was tested. No match means '
                 'no matching documented record here, not proof that an idea is new.',
        'counts': {'records': len(records),
                   'batch_suites': sum(bool(record.get('batch')) for record in records),
                   'batch_configurations': sum(record.get('batch', {}).get('case_count', 0) for record in records)},
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
    print(f'Published {len(records)} experiment records with stated review status')
    return records


if __name__ == '__main__':
    build()
