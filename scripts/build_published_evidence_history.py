"""Append immutable published proof envelopes; Git is only an explicit bootstrap source."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
HISTORY = 'data/published-evidence-history.json'
JAVASCRIPT = 'published-evidence-history-data.js'
CURRENT = ('data/published-count-evidence.json', 'data/published-opening-evidence.json')
BUDGET = {'bytes': 8 * 1024 * 1024, 'receipts': 256, 'tasks': 128, 'results': 128, 'seedSources': 1024}


def stable(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode('utf-8')).hexdigest()


def validate(value, registry=False):
    # Validation is the production count/program adapter plus current-engine
    # complete replay, not a second implementation of provenance semantics.
    command = ['node', str(ROOT / 'scripts/check_published_evidence_history.mjs')]
    if registry:
        command.append('--registry')
    subprocess.run(command, input=stable(value), check=True, capture_output=True, text=True, encoding='utf-8')


def empty():
    return {'schema': 'liberpedia-published-evidence-history-v1', 'tasks': [], 'results': [], 'receipts': [], 'seedSources': []}


def merge(history, manifests, seeds=()):
    """Append only. An existing tuple/body can never silently change or vanish."""
    validate(history)
    tasks = {item['id']: item for item in history['tasks']}
    results = {item['id']: item for item in history['results']}
    receipts = {(r['recordId'], r['revision'], r['caseId']): r for r in history['receipts']}
    seed_sources = {(s['commit'], s['path']): s for s in history['seedSources']}

    def add(mapping, key, value):
        if key in mapping and stable(mapping[key]) != stable(value):
            raise ValueError('Immutable published proof identity was reused with different bytes: ' + str(key))
        mapping[key] = value

    for manifest in manifests:
        validate(manifest, registry=True)
        records = {r['recordId']: r for r in manifest['records']}
        for entry in manifest['entries']:
            run, task = entry['run'], entry['task']
            add(tasks, task['taskId'], {'id': task['taskId'], 'task': task})
            add(results, run['id'], {'id': run['id'], 'result': run['result']})
            receipt = {'recordId': entry['recordId'], 'revision': entry['revision'], 'caseId': entry['caseId'], 'registrySchema': manifest['schema'], 'taskId': task['taskId'], 'resultId': run['id'], 'inputVersion': entry['inputVersion'], 'createdAt': run['createdAt'], 'provenance': records[entry['recordId']]['provenance']}
            add(receipts, (entry['recordId'], entry['revision'], entry['caseId']), receipt)
    for seed in seeds:
        add(seed_sources, (seed['commit'], seed['path']), seed)
    merged = {'schema': history['schema'], 'tasks': [tasks[k] for k in sorted(tasks)], 'results': [results[k] for k in sorted(results)], 'receipts': [receipts[k] for k in sorted(receipts)], 'seedSources': [seed_sources[k] for k in sorted(seed_sources)]}
    if len(stable(merged).encode('utf-8')) > BUDGET['bytes'] or any(len(merged[k]) > BUDGET[k] for k in ['tasks', 'results', 'receipts', 'seedSources']):
        raise ValueError('Published proof retention budget exceeded; no receipts may be evicted')
    validate(merged)
    return merged


def public_git_sources(root=ROOT):
    """One-time local-object import limited to the known published branch ancestry."""
    commits = subprocess.run(['git', 'log', 'origin/main', '--format=%H', '--', *CURRENT], cwd=root, check=True, capture_output=True, text=True).stdout.splitlines()
    manifests, seeds = [], []
    for commit in sorted(set(commits)):
        subprocess.run(['git', 'merge-base', '--is-ancestor', commit, 'origin/main'], cwd=root, check=True, capture_output=True)
        for name in CURRENT:
            exists = subprocess.run(['git', 'cat-file', '-e', commit + ':' + name], cwd=root, capture_output=True)
            if exists.returncode:
                continue
            raw = subprocess.run(['git', 'show', commit + ':' + name], cwd=root, check=True, capture_output=True).stdout
            manifests.append(json.loads(raw))
            seeds.append({'commit': commit, 'path': name, 'sha256': sha(raw)})
    if not manifests:
        raise ValueError('No published manifest ancestry was available for explicit seeding')
    return manifests, seeds


def build(root=ROOT, write=True, seed_public_git=False):
    path = root / HISTORY
    if path.exists():
        history = json.loads(path.read_bytes())
    elif seed_public_git:
        history = empty()
    else:
        raise ValueError('Published proof history is missing; bootstrap explicitly rather than forget old revisions')
    manifests = [json.loads((root / name).read_bytes()) for name in CURRENT]
    seeds = []
    if seed_public_git:
        seeded, seeds = public_git_sources(root)
        manifests.extend(seeded)
    merged = merge(history, manifests, seeds)
    content = stable(merged)
    javascript = "/* Generated immutable published proof history; discovery stays current-only. */\n(function(root){'use strict';const data=" + content + ";function freeze(v){if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;}freeze(data);if(typeof module==='object'&&module.exports)module.exports=data;else root.PublishedEvidenceHistoryData=data;})(typeof globalThis!=='undefined'?globalThis:this);\n"
    artifacts = {HISTORY: content + '\n', JAVASCRIPT: javascript}
    if not write:
        for name, value in artifacts.items():
            if not (root / name).exists() or (root / name).read_text(encoding='utf-8') != value:
                raise ValueError('Stale immutable published proof history: ' + name)
    else:
        # Every source/receipt is validated before either artifact is written.
        for name, value in artifacts.items():
            (root / name).write_text(value, encoding='utf-8', newline='\n')
    return merged


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--seed-public-git', action='store_true', help='Explicit one-time import from local origin/main public ancestry')
    args = parser.parse_args()
    result = build(write=not args.check, seed_public_git=args.seed_public_git)
    print('Immutable published proofs: ' + str(len(result['receipts'])) + ' envelopes, ' + str(len(result['tasks'])) + ' task bodies, ' + str(len(result['results'])) + ' result bodies.')
