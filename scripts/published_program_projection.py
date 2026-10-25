"""Explicit fixed-program projections of archived exclusions, never historical runs."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE = 'experiments/records/prepared-opening-evidence-gates'
DECLARATION = {
    'recordId': 'prepared-opening-evidence-gates',
    'id': 'row-reversal-atbash-warning',
    'ownerRecordId': 'lp2-row-column-routes',
    'followupId': 'row-reversal-atbash-warning',
    'checkedAt': '2026-10-25T00:00:00.000Z',
    'steps': [{'op': 'reverse', 'unit': 'line'}, {'op': 'affine', 'a': 28, 'b': 28}],
    'criterion': {'kind': 'exact-prefix', 'values': [24, 7, 24, 4, 9, 21, 17, 18, 20, 10, 18, 1, 18, 9, 3, 2, 21, 0, 4, 3, 19, 2, 10, 15]},
    'sourceSha256': {
        f'{BASE}/plan.json': '599a0d2d8f4f86d9df931a832c6de9b3471e3b9a869bfd69ad20a77589417cf3',
        f'{BASE}/results.json': 'e665db6ae6edac4faac013d0582f2221b95daf53c8c7f05907787f801589b453',
        f'{BASE}/run.py': '9cac549e1800d25c9ac9075464df5abf83b407d938facdd7290e90dd6dfccc26',
        f'{BASE}/check.py': '1c8253bf799a45be6837b4b03c06162b2cd8ffc21c149741e14df0b68dd9431d',
        'scripts/prefix_evidence_gate.py': '4791ae5fb6d8328070c7359fde304fc0b816c0764a97cd8336f102f257eafa15',
    },
    # The historical checker pins recipe titles alongside mathematical fields.
    # Restore only these known original titles in its disposable source mirror;
    # the pinned projection hash still verifies every active mathematical field.
    'historicalRecipeTitles': {
        'cumulative-word-reset-warning': 'Restart the cumulative rule at each word',
        'cumulative-line-reset-warning': 'Restart the cumulative rule at each line',
        'row-reversal-atbash-warning': 'Reverse each line, then apply Atbash',
        'word-reversal-atbash-warning': 'Reverse each word, then apply Atbash',
    },
}


def stable(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode('utf-8')).hexdigest()


def source_files(root=ROOT):
    """Everything needed by the original independent checker, including records."""
    plan = json.loads((root / BASE / 'plan.json').read_bytes())
    return sorted(set(DECLARATION['sourceSha256']) | {p['path'] for p in plan['inputs']}
                  | {p['path'] for p in plan['recipe_identities']})


def check_original(root, plan):
    # No archived/repository file is modified. Prose changes do not alter the
    # archived mathematical claim, and the exact original checker runs intact.
    with tempfile.TemporaryDirectory(prefix='liberpedia-opening-check-') as temp:
        mirror = Path(temp)
        for name in source_files(root):
            target = mirror / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / name, target)
        for identity in plan['recipe_identities']:
            target = mirror / identity['path']
            record = json.loads(target.read_bytes())
            recipe = next(r for r in record['browser_followups'] if r['id'] == identity['id'])
            recipe['title'] = DECLARATION['historicalRecipeTitles'][identity['id']]
            projection = {k: recipe[k] for k in ('id', 'title', 'card', 'inputs', 'control')}
            if sha(stable(projection)) != identity['sha256']:
                raise ValueError('The archived source recipe changed its mathematical definition')
            target.write_text(json.dumps(record, ensure_ascii=False), encoding='utf-8')
        subprocess.run(['python', str(mirror / BASE / 'check.py')], cwd=mirror, check=True, capture_output=True, text=True)


def independent_row_atbash(text, alphabet):
    """Ordering by physical text-line keys, independent of the JS flush loop."""
    lookup = {row['rune']: i for i, row in enumerate(alphabet)}
    lines = defaultdict(list)
    line = 0
    for offset, char in enumerate(text):
        if char in lookup:
            lines[line].append(offset)
        elif char in '\r\n':
            line += 1
    source_offsets = [offset for positions in lines.values() for offset in reversed(positions)]
    positions = [i for i, char in enumerate(text) if char in lookup]
    before = [lookup[text[i]] for i in source_offsets]
    after = [(28 - n) % 29 for n in before]
    output = list(text)
    for target, value in zip(positions, after):
        output[target] = alphabet[value]['rune']
    return {'text': ''.join(output), 'before': before, 'after': after, 'sourceOffsets': source_offsets}


def build(root=ROOT, write=True):
    declaration = DECLARATION
    pins = dict(declaration['sourceSha256'])
    for name, expected in pins.items():
        if sha((root / name).read_bytes()) != expected:
            raise ValueError('Published program source pin changed: ' + name)
    plan = json.loads((root / BASE / 'plan.json').read_bytes())
    if len(plan['inputs']) != 65 or len(plan['pages']) != 55 or plan['pages'] != [f'lp2-{n:02d}' for n in range(56) if n != 50]:
        raise ValueError('The archived program input domain changed')
    for item in plan['inputs']:
        if item['path'] in pins or sha((root / item['path']).read_bytes()) != item['sha256']:
            raise ValueError('Published program input pin changed: ' + item['path'])
        pins[item['path']] = item['sha256']
    report = json.loads((root / BASE / 'results.json').read_bytes())
    if report['schema'] != 'liberpedia-prefix-evidence-gates-v1' or report['plan_sha256'] != pins[f'{BASE}/plan.json'] or report['opening_indices'] != declaration['criterion']['values']:
        raise ValueError('The archived report describes a different program question')
    check_original(root, plan)
    alphabet = [{k: row[k] for k in ('rune', 'latin', 'prime')} for row in json.loads((root / 'data/index.json').read_bytes())['alphabet']]
    owner = json.loads((root / f"experiments/records/{declaration['ownerRecordId']}/record.json").read_bytes())
    recipe = next(r for r in owner['browser_followups'] if r['id'] == declaration['followupId'])
    inputs = recipe['inputs']
    if inputs['version'] != 'raw' or inputs['alphabet_sha256'] != sha(stable(alphabet)) or inputs['pages'] != [{'id': pid, 'text_sha256': pins[f'text/{pid}.txt']} for pid in plan['pages']]:
        raise ValueError('The owned recipe input definition changed')
    texts = [{'id': pid, 'text': (root / f'text/{pid}.txt').read_bytes().decode('utf-8')} for pid in plan['pages']]
    official = json.loads((root / 'data/local-run-inputs.json').read_bytes())
    if official['alphabet'] != alphabet or any(next(p['raw'] for p in official['pages'] if p['id'] == item['id']) != item['text'] for item in texts):
        raise ValueError('Current browser inputs differ from the archived program sources')
    witnesses = next(row for row in report['recipes'] if row['id'] == declaration['id'])
    saved = json.loads((root / 'experiments/records/lp2-row-column-routes/results.json').read_bytes())
    rows = {row['page']: row for row in saved['pages']}
    independently = {}
    if witnesses['closed_pages'] != 55 or [w['page'] for w in witnesses['pages']] != plan['pages']:
        raise ValueError('The archived exclusion page coverage changed')
    for page, witness in zip(texts, witnesses['pages']):
        result = independent_row_atbash(page['text'], alphabet)
        route = [case for case in rows[page['id']]['cases'] if case.get('axis') == 'row' and case.get('outer_reverse') is False and case.get('inner_reverse') is True and case.get('alternating') is False]
        mismatch = next((i for i, (a, b) in enumerate(zip(result['after'], declaration['criterion']['values'])) if a != b), None)
        take = mismatch + 1 if mismatch is not None else 0
        if len(route) != 1 or route[0]['output_indices'] != result['before'] or mismatch is None or witness['excluded'] is not True or witness['first_mismatch_zero_based'] != mismatch or witness['saved_output_prefix'] != result['before'][:take] or witness['source_input_prefix'] != result['before'][:take] or witness['source_character_offsets'] != result['sourceOffsets'][:take] or witness['required_preimage_prefix'] != [(28 - n) % 29 for n in declaration['criterion']['values'][:take]]:
            raise ValueError('Archived witness disagrees with independent fixed-program replay')
        independently[page['id']] = result
    payload = {'title': 'Published fixed-program check · ' + declaration['id'], 'pages': texts, 'alphabet': alphabet, 'steps': declaration['steps'], 'criterion': declaration['criterion']}
    code = """const fs=require('node:fs'),c=require('node:crypto'),E=require(process.argv[1]);(async()=>{const task=await E.prepare(JSON.parse(fs.readFileSync(0,'utf8'))),result=await E.verify(task,E.run(task));console.log(JSON.stringify({task,result,id:c.createHash('sha256').update(E.stable(result)).digest('hex')}));})().catch(e=>{console.error(e);process.exitCode=1;});"""
    browser = json.loads(subprocess.run(['node', '-e', code, str(root / 'local-experiment.js')], input=json.dumps(payload, ensure_ascii=False), cwd=root, check=True, capture_output=True, text=True, encoding='utf-8').stdout)
    if browser['result']['transformed'] != [{'page': page['id'], 'text': independently[page['id']]['text']} for page in texts] or browser['result']['matches'] != [{'page': page['id'], 'matched': False} for page in texts]:
        raise ValueError('Browser program and independent Python replay disagree')
    # Current verification code is revision-bound separately from archived pins.
    for name in ['local-experiment.js', 'scripts/published_program_projection.py']:
        pins[name] = sha((root / name).read_bytes().replace(b'\r\n', b'\n'))
    projection = {'id': declaration['id'], 'ownerRecordId': declaration['ownerRecordId'], 'followupId': declaration['followupId'], 'inputVersion': 'raw', 'steps': declaration['steps'], 'criterion': declaration['criterion'], 'pages': plan['pages'], 'alphabetSha256': inputs['alphabet_sha256'], 'taskId': browser['task']['taskId'], 'resultId': browser['id']}
    provenance = {'schema': 'liberpedia-published-program-projection-v1', 'recordId': declaration['recordId'], 'projection': projection, 'sourcePins': [{'path': name, 'sha256': value} for name, value in sorted(pins.items())], 'checkedAt': declaration['checkedAt'], 'dateMeaning': 'Fixed-program reproduction checked on this date; not a historical browser submission.', 'verificationMeaning': 'Original finite exclusion witnesses checked independently. Complete outputs freshly reproduced by independent Python and the fixed browser engine; the archived report did not contain these full transformed outputs.'}
    revision = sha(stable(provenance))
    manifest = {'schema': 'liberpedia-published-program-evidence-v1', 'records': [{'recordId': declaration['recordId'], 'revision': revision, 'provenance': provenance}], 'entries': [{'recordId': declaration['recordId'], 'revision': revision, 'caseId': declaration['id'] + '--all-pages', 'task': browser['task'], 'inputVersion': 'raw', 'run': {'id': browser['id'], 'createdAt': declaration['checkedAt'], 'result': browser['result']}}]}
    content = json.dumps(manifest, ensure_ascii=False, separators=(',', ':'))
    javascript = "/* Generated fixed-program evidence. */\n(function(root){'use strict';const data=" + content + ";function freeze(v){if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;}freeze(data);if(typeof module==='object'&&module.exports)module.exports=data;else root.PublishedProgramEvidenceData=data;})(typeof globalThis!=='undefined'?globalThis:this);\n"
    for name, value in {'data/published-opening-evidence.json': content + '\n', 'published-opening-evidence-data.js': javascript}.items():
        if write:
            (root / name).write_text(value, encoding='utf-8', newline='\n')
        elif not (root / name).exists() or (root / name).read_text(encoding='utf-8') != value:
            raise ValueError('Stale published program evidence: ' + name)
    return manifest
