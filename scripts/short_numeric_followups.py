"""Propose one source-owned short-key restart family; synthetic controls only."""
import ast
import copy
import hashlib
import json
import re
from pathlib import Path

import authored_finite_followups as authored
import finite_control_storage as storage
import browser_boundary_variations as boundary
import browser_followups as fixed
from research_questions import validate_research_questions

ROOT = Path(__file__).resolve().parents[1]
RECORD = 'dukotah-fixed-numeric-keys'
BASE = 'experiments/records/' + RECORD
IDENTIFIER = 'short-numeric-keys-reset-language'
PAGES = ['lp2-%02d' % n for n in range(56) if n != 50]
PINS = {'plan.json': 'c322ade351ca17bd617bf2ac4ac05b044baae8764cd8be0e2dc17ee552ef6735',
        'results.json': 'dd9a2715e7746f1e7b9e64a2ad4837ce0c5a9184aef35cc82e3440adfd432e4a',
        'run.py': '1f00ed9181c857242a384379da546f63cb4246983878b368292da77e1ac49ef9',
        'check.py': 'b2e2362ce4c8e1f95a0f5cf780011b0135a188ed32a93edf7e2b44721c5da2c4'}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def literal(path, name):
    """Read a single literal assignment; never import or execute source code."""
    nodes = [node.value for node in ast.parse(path.read_text(encoding='utf-8')).body
             if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)]
    fixed.require(len(nodes) == 1, 'source literal assignment changed: ' + name)
    return ast.literal_eval(nodes[0])


def source(root=ROOT):
    root = Path(root)
    pins = {}
    def pin(path, expected):
        target = (root / path).resolve()
        fixed.require(target.is_relative_to(root.resolve()), 'source pin escapes root')
        raw = target.read_bytes()
        fixed.require(digest(raw) == expected, 'source pin changed: ' + path)
        pins[path] = expected
        return raw
    frozen = {name: pin(BASE + '/' + name, sha) for name, sha in PINS.items()}
    plan, results = json.loads(frozen['plan.json']), json.loads(frozen['results.json'])
    record = json.loads((root / BASE / 'record.json').read_bytes())
    fixed.require(record['id'] == plan['record_id'] == RECORD and record['status'] == 'published', 'source ownership changed')
    fixed.require(plan['source_revision'] == results['source_revision'] == 'f08b20b632d91209ddbaa747e8e2f23df0c78ba1'
                  and results['plan_sha256'] == PINS['plan.json'] and results['case_count'] == 5376
                  and results['control_count'] == 288 and results['source_bar'] == -5.2, 'archived source bounds changed')
    for name, sha in plan['source_files_sha256'].items():
        pin(BASE + '/source/' + name, sha)
    for entry in record['reproduction']['inputs']:
        pin(entry['path'], entry['sha256'])
    source_dir = root / BASE / 'source/analysis/campaign7'
    mayan = literal(source_dir / 'b1_mayan.py', 'MAYAN')
    cuneiform = literal(source_dir / 'c2_cuneiform.py', 'KEYS')
    hex_string = literal(source_dir / 'b4_hash_kdf.py', 'HEX')
    fixed.require(mayan == [10, 2, 14, 7, 19, 6, 18, 12, 7, 8, 17, 0, 19], 'Mayan source key changed')
    fixed.require(cuneiform == {'cuneiform_17_13_55_1': [17, 13, 55, 1], 'cuneiform_rev': [1, 55, 13, 17],
                  'digits_1033': [1, 0, 3, 3], 'digits_3301': [3, 3, 0, 1],
                  'cuneiform+1033+3301': [17, 13, 55, 1, 1, 0, 3, 3, 3, 3, 0, 1]}, 'cuneiform source keys changed')
    page56 = json.loads((root / 'data/pages/lp2-56.json').read_bytes())
    printed = ''.join(line['raw'].strip('/') for line in page56['lines'] if re.fullmatch(r'[0-9a-f]+/', line['raw']))
    fixed.require(printed == hex_string and len(hex_string) == 128, 'printed hash no longer matches source bytes')
    pins['data/pages/lp2-56.json'] = digest((root / 'data/pages/lp2-56.json').read_bytes())
    named = [('B1', 'mayan_fwd', mayan), ('B1', 'mayan_rev', mayan[::-1]),
             ('B4', 'hash_bytes', list(bytes.fromhex(hex_string))),
             ('B4', 'hash_hexdigits', [int(c, 16) for c in hex_string]),
             *[('C2', name, values) for name, values in cuneiform.items()]]
    keys = [{'branch': branch, 'id': name, 'indices': [n % 29 for n in values]} for branch, name, values in named]
    fixed.require(len(keys) == 9 and len({tuple(key['indices']) for key in keys}) == 9, 'short source keys are not distinct')
    alphabet = fixed.alphabet(root)
    lookup = {a['rune']: n for n, a in enumerate(alphabet)}
    archived = (root / BASE / 'source/data/krisyotam_runes.txt').read_text(encoding='utf-8')
    vectors = [[lookup[ch] for ch in page if ch in lookup] for page in archived.split('%')]
    vectors = [values for values in vectors if values]
    fixed.require(len(vectors) == 57, 'source rune page mapping changed')
    bundle = json.loads((root / 'data/local-run-inputs.json').read_bytes())
    fixed.require(bundle['alphabet'] == alphabet, 'official alphabet differs')
    for page_id, expected in zip(PAGES, vectors[:-2]):
        raw = (root / 'text' / (page_id + '.txt')).read_bytes()
        text = raw.decode('utf-8')
        page = json.loads((root / 'data/pages' / (page_id + '.json')).read_bytes())
        fixed.require(text == page['raw'] == next(p['raw'] for p in bundle['pages'] if p['id'] == page_id)
                      and [lookup[ch] for ch in text if ch in lookup] == expected, 'official raw input differs: ' + page_id)
        pins['text/' + page_id + '.txt'] = digest(raw)
    fixed.require(sum(map(len, vectors[:-2])) == 12956, 'source rune total changed')
    identities = {(row['branch'], row['key']) for row in results['rows']}
    fixed.require(all((key['branch'], key['id']) in identities for key in keys), 'named short source keys missing from archive')
    fixed.require(sum(row['target'] in PAGES and row['atbash'] == 0 and row['interrupter'] == 0
                      and (row['branch'], row['key']) in {(k['branch'], k['id']) for k in keys}
                      for row in results['rows']) == 990, 'plain-clock page baseline changed')
    return {'record': record, 'keys': keys, 'pins': [{'path': p, 'sha256': sha} for p, sha in sorted(pins.items())]}


def provenance(root=ROOT):
    return copy.deepcopy(source(root)['pins'])


def candidate(root=ROOT):
    declared = source(root)
    specified = lambda value: {'status': 'specified', 'value': value}
    rules = {name: {'status': 'unspecified'} for name in fixed.RULES}
    for name, value in {'representation': 'GP29', 'wordBoundaries': 'preserve', 'unmapped': 'preserve',
                        'inputVersion': 'raw', 'evaluation': copy.deepcopy(fixed.LANGUAGE_CRITERION),
                        'searchBounds': {'kind': 'finite-settings', 'version': 1, 'parameters': [
                            {'operation': 0, 'name': 'key', 'values': [k['indices'] for k in declared['keys']]},
                            {'operation': 0, 'name': 'direction', 'values': ['subtract', 'add']}]}}.items():
        rules[name] = specified(value)
    baseline = {'version': 1, 'outcome': specified({'outcomeId': 'decipher', 'detail': 'Decipher the text'}),
                'method': specified({'operations': [{'id': 'repeating_key', 'reset': 'page'}]}),
                'scope': specified({'pages': PAGES[:]}), 'rules': rules, 'unresolved': []}
    card = boundary.family(baseline, operation_index=0, allowed_resets=['page', 'line', 'word'])['card']
    return authored.construct_followup(root, card=card, identifier=IDENTIFIER,
        title='Try the short number patterns with three restart rules',
        question='Do the nine short source number patterns produce outputs resembling the maintained language samples when restarted at each page, line or word?',
        scope_change='Use all nine source keys that fit the repeating-key adapter, both directions and the same 55 rune-bearing pages. Keep the original page restart and add line and word restarts, always at starting place zero.',
        limitation='Language similarity is not a reading or an improvement over the earlier scorer. No Atbash, F interruption, long derived keys, joined whole-book stream or other starting places. Line restarts follow line breaks; word restarts also happen at spaces and punctuation. These are new runs, not reused archived outputs.',
        motivation='The archived scripts tried two listed rotation patterns, five short numeral patterns, and two versions of the printed hash as numbers. Try these nine repeating patterns with three restart rules. Compare language samples rather than the earlier English score; the numerical origins do not prove a decoding method.')


def questions():
    return [{'id': IDENTIFIER, 'state': 'open', 'note': 'A new language comparison with three explicit restart rules. Earlier English-scoring findings are unchanged; no outputs are asserted here.',
             'records': [], 'followup': IDENTIFIER, 'protocol': {'id': 'finite-settings-output', 'version': 1}}]



def semantic_recipe(recipe):
    value = copy.deepcopy(recipe)
    value['control'] = storage.expand(value['control'])
    return value

def proposed(root=ROOT):
    root = Path(root)
    result = copy.deepcopy(source(root)['record'])
    recipe = candidate(root)
    existing = next((r for r in result.get('browser_followups', []) if r['id'] == IDENTIFIER), None)
    fixed.require(existing is None or semantic_recipe(existing) == semantic_recipe(recipe), 'existing short-key recipe changed')
    result['browser_followups'] = [r for r in result.get('browser_followups', []) if r['id'] != IDENTIFIER] + [recipe]
    result['research_questions'] = [q for q in result.get('research_questions', []) if q['id'] != IDENTIFIER] + questions()
    validate_research_questions(result['research_questions'], result, strict_authoring=True)
    fixed.require(len(json.dumps(result, ensure_ascii=False, separators=(',', ':')).encode()) < 2 * 1024 * 1024,
                  'proposed source exceeds 2 MiB')
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify installed declarations match the source-built proposal; never run manuscript tests')
    parser.add_argument('--output', type=Path, help='Write the detached proposal only inside outer qa-temp')
    args = parser.parse_args()
    value = proposed()
    if args.check:
        installed = json.loads((ROOT / BASE / 'record.json').read_text(encoding='utf-8'))
        fixed.require(installed == value, 'installed short-key declarations differ from the source-built proposal')
    if args.output:
        destination = args.output.resolve()
        fixed.require(destination.is_relative_to((ROOT.parent.parent / 'qa-temp').resolve()), 'private output must stay inside outer qa-temp')
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    print(json.dumps({'recordId': RECORD, 'programs': 54, 'pages': 55, 'cases': 2970, 'syntheticWarningControls': 54,
                      'targetExecutions': 0, 'installed': bool(args.check)}))
