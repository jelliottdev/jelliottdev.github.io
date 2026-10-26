"""Offline full-Warning commitments. Only synthetic ciphertext is executed.

No target outputs, publication, admission or coverage are produced. Default CLI
prints a detached report. Explicit output is restricted to repository qa-temp.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

import browser_followups as fixed
import build_local_run_inputs as inputs
import pinned_domain_partitions as P

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'liberpedia-pinned-control-commitments-v1'
TEMPLATE = 'liberpedia-warning-template-v1'
ENCODER = 'warning-inverse-v1'
SOURCE_PATHS = ('data/pages/lp1-01.json', 'exports/readings/warning.csv',
                'scripts/browser_followups.py', 'tools/research_runner.py')


def source_pins(root, paths):
    root = Path(root).resolve()
    result = []
    for path in sorted(set(paths)):
        target = (root / path).resolve()
        fixed.require(target.is_relative_to(root), 'control source escapes root')
        result.append(dict(path=path, sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
    return result


def template(root=ROOT):
    root = Path(root)
    before = source_pins(root, SOURCE_PATHS)
    alphabet = fixed.alphabet(root)
    fixed.require(fixed.digest(alphabet) == P.ALPHABET, 'official alphabet changed')
    plaintext, values = fixed.warning_plaintext(root, alphabet)
    fixed.require(len(values) == 184, 'control must cover all 184 Warning runes')
    fixed.require(source_pins(root, SOURCE_PATHS) == before, 'Warning sources changed during construction')
    return dict(schema=TEMPLATE, alphabetSha256=P.ALPHABET, plaintext=plaintext,
                values=values, sourcePins=before)


def _bind(root, parent, bundle, registry):
    root = Path(root).resolve()
    original = P.capture(parent)
    registry = P.MaintainedRegistry() if registry is None else registry
    plan = P.prepare(original, registry)
    official_bytes = inputs.render(root)
    official = json.loads(official_bytes)
    # Do not let caller data substitute for any official page, even unselected ones.
    supplied = json.loads((root / 'data/local-run-inputs.json').read_bytes()) if bundle is None else P.capture(bundle)
    fixed.require(P.stable(supplied) == P.stable(official), 'complete official input bundle changed')
    fixed.require(fixed.digest(official['alphabet']) == original['alphabetSha256'] == P.ALPHABET,
                  'official alphabet changed')
    indexed = {p['id']: p for p in official['pages']}
    pages = []
    for pin in original['pages']:
        text = indexed[pin['id']]['raw' if original['inputVersion'] == 'raw' else 'reviewed_text']
        fixed.require(type(text) is str and fixed.text_hash(text) == pin['textSha256'], 'full parent page pin changed')
        pages.append(dict(id=pin['id'], text=text))
    paths = [p['path'] for p in original['sourcePins']] + list(SOURCE_PATHS)
    paths += ['data/index.json', 'data/local-run-inputs.json'] + ['data/pages/' + p['id'] + '.json' for p in original['pages']]
    guard = source_pins(root, paths)
    actual = {p['path']: p['sha256'] for p in guard}
    fixed.require(all(actual[p['path']] == p['sha256'] for p in original['sourcePins']), 'declared source pin changed')
    known = template(root)
    def unchanged():
        fixed.require(P.stable(P.capture(parent)) == P.stable(original), 'parent changed during controls')
        fixed.require(source_pins(root, paths) == guard, 'source changed during controls')
        if bundle is not None:
            fixed.require(P.stable(P.capture(bundle)) == P.stable(official), 'bundle changed during controls')
    unchanged()
    return original, plan, official['alphabet'], pages, known, registry, unchanged


def actual_steps(parent, key, pages, alphabet):
    """Same bounded representation as PinnedDomainMembers, using full-parent scope."""
    fixed.require(P.vector(key, 20000), 'invalid complete source key')
    steps = copy.deepcopy(parent['steps'])
    step = steps[parent['keyOperation']]
    step['key'] = key[:]
    if step['op'] == 'keyed-shift' and len(key) > 256:
        fixed.require(step['mode'] == 'repeat', 'oversized autokey cannot be replaced')
        runes = {a['rune'] for a in alphabet}
        maximum = 0
        for page in pages:
            segment = 0
            for ch in page['text']:
                if ch in runes:
                    segment += 1
                    maximum = max(maximum, segment)
                elif step['reset'] == 'word' or step['reset'] == 'line' and ch in '\r\n':
                    segment = 0
        cycles = max(1, math.ceil(maximum / len(key)))
        fixed.require(cycles * len(key) <= 20000, 'complete periodic stream exceeds 20000 values')
        steps[parent['keyOperation']] = dict(op='finite-shift', key=key * cycles,
                                            direction=step['direction'], reset=step['reset'])
    return steps


def _witness(parent, domain_id, index, key, pages, alphabet, known):
    steps = actual_steps(parent, key, pages, alphabet)
    encoded = known['plaintext']
    for step in reversed(steps):
        encoded = fixed.inverse_step(encoded, step, alphabet)
    task = dict(schema=fixed.runner.TASK_SCHEMA, engine=fixed.runner.ENGINE,
                title='Synthetic complete-output pinned control: ' + domain_id + ' setting ' + str(index + 1),
                pages=[dict(id='lp1-01', text=encoded)], alphabet=copy.deepcopy(alphabet),
                steps=steps, criterion=dict(kind='exact-prefix', values=known['values'][:]))
    task['taskId'] = fixed.runner.task_identity(task)
    # This is the ONLY scientific execution here: one synthetic full-output input.
    result = fixed.runner.run(task)
    fixed.require(result['transformed'] == [dict(page='lp1-01', text=known['plaintext'])]
                  and result['matches'] == [dict(page='lp1-01', matched=True)], 'complete Warning control failed')
    return dict(task=task, result=result, entry=[task['taskId'], fixed.digest(result)])


def witness(root, parent, global_index, *, bundle=None, registry=None):
    d, plan, alphabet, pages, known, registry, unchanged = _bind(root, parent, bundle, registry)
    fixed.require(P.integer(global_index, 0, d['bank']['count'] - 1), 'invalid global setting index')
    keys = P.capture(registry.resolve({**d['bank'], 'start': global_index, 'count': 1}), P.MAX)
    fixed.require(type(keys) is list and len(keys) == 1, 'source truncated selected key')
    value = _witness(d, plan['domainId'], global_index, keys[0], pages, alphabet, known)
    unchanged()
    return value


def build(root, parent, *, bundle=None, registry=None):
    d, plan, alphabet, pages, known, registry, unchanged = _bind(root, parent, bundle, registry)
    entries, seen = [], set()
    for start in range(0, d['bank']['count'], 128):
        count = min(128, d['bank']['count'] - start)
        keys = P.capture(registry.resolve({**d['bank'], 'start': start, 'count': count}), P.MAX)
        fixed.require(type(keys) is list and len(keys) == count, 'source truncated control keys')
        for offset, key in enumerate(keys):
            signature = P.stable(key)
            fixed.require(P.vector(key, 20000) and signature not in seen, 'source key changed or repeated')
            seen.add(signature)
            entries.append(_witness(d, plan['domainId'], start + offset, key, pages, alphabet, known)['entry'])
        unchanged()
    fixed.require(len(entries) == d['bank']['count'], 'incomplete control commitments')
    merged = {p['path']: p['sha256'] for p in d['sourcePins']}
    for pin in known['sourcePins']:
        fixed.require(pin['path'] not in merged or merged[pin['path']] == pin['sha256'], 'conflicting control source pin')
        merged[pin['path']] = pin['sha256']
    manifest = dict(schema=SCHEMA, parentDomainId=plan['domainId'], templateSha256=fixed.digest(known),
                    encoder=ENCODER, sourcePins=[dict(path=path, sha256=sha) for path, sha in sorted(merged.items())], entries=entries)
    unchanged()
    return dict(template=known, manifest=manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    output = None
    if args.output_dir is not None:
        output = args.output_dir.resolve()
        allowed = [ROOT / 'qa-temp', ROOT.parent.parent / 'qa-temp']
        parser_error = not any(output.is_relative_to(p.resolve()) and output != p.resolve() for p in allowed)
        if parser_error:
            parser.error('--output-dir must be a dedicated folder inside inner or outer qa-temp')
    import rotating_domain_sources
    report = []
    for variant, parent in rotating_domain_sources.domains(ROOT).items():
        value = build(ROOT, parent)
        manifest_bytes = (P.stable(value['manifest']) + '\n').encode('utf-8')
        if output is not None:
            output.mkdir(parents=True, exist_ok=True)
            for filename, raw in ((variant + '-controls.json', manifest_bytes),
                                  ('warning-template.json', (P.stable(value['template']) + '\n').encode('utf-8'))):
                target = output / filename
                fixed.require(target.resolve().is_relative_to(output), 'output artifact escapes its private folder')
                target.write_bytes(raw)
        report.append(dict(variant=variant, parentDomainId=value['manifest']['parentDomainId'],
                           entries=len(value['manifest']['entries']), manifestSha256=hashlib.sha256(manifest_bytes).hexdigest(),
                           templateSha256=value['manifest']['templateSha256']))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
