"""Check experiment archives and rerun representative scripts in isolation."""
import argparse
import hashlib
import json
from pathlib import Path
import posixpath
import subprocess
import sys
import tempfile
import zipfile
from verify_bundle import verify

ROOT = Path(__file__).resolve().parents[1]

# These are rebuilt from the registry/content during a release. They are not
# inputs to the experiment bundles unless a record explicitly declares one.
GENERATED_RELEASE_OUTPUTS = {
    'data/catalog.json',
    'data/experiment-index.json',
    'data/checker-records.json',
    'data/articles.json',
    'data/article-search.json',
    'data/guide-index.json',
    'data/method-families.json',
    'data/research-map.json',
    'downloads/SHA256SUMS.txt',
    'downloads/reference-data.zip',
}

# This browser retrieval regression neither builds nor verifies archive members.
# If a record declares it as an input, the dependency lookup below still wins.
UNRELATED_CHECKS = {'scripts/test_assistant.cjs'}


def _git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True, check=True)


def select_records(root, records, ref):
    """Return (selected IDs, reason); uncertainty selects all, never a subset."""
    all_ids = {record['id'] for record in records}
    try:
        top = Path(_git(root, 'rev-parse', '--show-toplevel').stdout.decode().strip()).resolve()
        if top != root.resolve():
            raise ValueError('validation root is not the Git repository root')
        commit = _git(root, 'rev-parse', '--verify', '--end-of-options',
                      f'{ref}^{{commit}}').stdout.decode().strip()
        base = json.loads(_git(root, 'show', f'{commit}:data/experiments.json').stdout)['records']
        diff = _git(root, 'diff', '--name-only', '-z', '--no-ext-diff', commit, '--').stdout
        staged = _git(root, 'diff', '--cached', '--name-only', '-z', '--no-ext-diff', commit, '--').stdout
        untracked = _git(root, 'ls-files', '--others', '--exclude-standard', '-z').stdout
    except (OSError, subprocess.CalledProcessError, ValueError, KeyError,
            UnicodeDecodeError, json.JSONDecodeError) as exc:
        return all_ids, f'full fallback: cannot establish a safe Git baseline ({exc})'

    base_by_id = {record['id']: record for record in base}
    current_by_id = {record['id']: record for record in records}
    if len(base_by_id) != len(base) or len(current_by_id) != len(records):
        return all_ids, 'full fallback: duplicate record ID in a registry'
    if set(base_by_id) - all_ids:
        return all_ids, 'full fallback: record removed since baseline'

    selected = {identifier for identifier, record in current_by_id.items()
                if record != base_by_id.get(identifier)}
    changed = {name.decode('utf-8').replace('\\', '/') for output in (diff, staged, untracked)
               for name in output.split(b'\0') if name}
    dependencies = {}
    for registry in (base, records):
        for record in registry:
            script = record.get('reproduction', {}).get('script')
            paths = ([script] if script else [])
            paths += [item['path'] for item in record.get('reproduction', {}).get('inputs', [])
                      + record.get('reproduction', {}).get('outputs', [])]
            paths += record.get('scope', {}).get('artifacts', [])
            for value in paths:
                if not isinstance(value, str):
                    return all_ids, 'full fallback: unrecognized dependency path'
                key = posixpath.normpath(value.replace('\\', '/'))
                if key.startswith(('/', '../')) or key in ('.', '..') or ':' in key:
                    return all_ids, 'full fallback: dependency outside a repository path'
                dependencies.setdefault(key, set()).add(record['id'])

    for name in changed:
        if ((name.startswith('scripts/') and name not in UNRELATED_CHECKS)
                or name.startswith(('experiments/engines/', 'experiments/suites/'))):
            return all_ids, f'full fallback: shared validator or engine changed ({name})'
        if name == 'downloads/original-images.zip':
            return all_ids, 'full fallback: shared original-image archive changed'
        # Scope artifacts may name a directory. A child change still affects
        # its consumers, including when the child is a generated output.
        matched = set()
        for ancestor in (name, *[str(p).replace('\\', '/') for p in Path(name).parents if str(p) != '.']):
            matched.update(dependencies.get(ancestor, ()))
        if matched:
            selected.update(matched & all_ids)
        if name == 'data/experiments.json':
            # Compare individual records, while retaining any declared consumer
            # of the registry itself or its containing directory.
            continue
        parts = name.split('/')
        if len(parts) >= 4 and parts[:2] == ['experiments', 'records']:
            if parts[2] in all_ids:
                selected.add(parts[2])
            continue
        if len(parts) == 3 and parts[:2] == ['downloads', 'experiments'] and name.endswith('.zip'):
            identifier = name.rsplit('/', 1)[-1][:-4]
            if identifier in all_ids:
                selected.add(identifier)
            continue
        if matched or name in GENERATED_RELEASE_OUTPUTS or name in UNRELATED_CHECKS:
            continue
        elif name.startswith(('data/', 'downloads/', 'experiments/')):
            return all_ids, f'full fallback: unclassified shared input changed ({name})'
    return selected, f'changed since {commit[:12]}'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--changed-from', metavar='REF', help='validate only safely affected bundles since REF')
    args = parser.parse_args(argv)
    records = json.loads((ROOT / "data/experiments.json").read_text(encoding="utf-8"))["records"]
    if args.changed_from:
        selected, reason = select_records(ROOT, records, args.changed_from)
    else:
        selected, reason = {record['id'] for record in records}, 'full validation (default/manual)'
    print(f'Experiment bundles: selected {len(selected)}/{len(records)} ({reason})', flush=True)
    if not selected:
        print('PASS: no experiment bundles changed; default/manual invocation validates all bundles.')
        return
    with zipfile.ZipFile(ROOT / 'downloads/original-images.zip') as original_archive:
        shared_originals = {item['path']: item for item in
                            json.loads(original_archive.read('ORIGINAL-IMAGES-CONTENTS.json'))}
    with tempfile.TemporaryDirectory(prefix="experiment-bundles-", dir=ROOT.parent) as folder:
        workspace = Path(folder).resolve()
        assert workspace.is_relative_to(ROOT.parent.resolve()) and workspace != ROOT
        for record in records:
            experiment_id = record["id"]
            if experiment_id not in selected:
                continue
            target = workspace / experiment_id
            target.mkdir()
            with zipfile.ZipFile(ROOT / "downloads/experiments" / f"{experiment_id}.zip") as archive:
                for name in archive.namelist():
                    assert (target / name).resolve().is_relative_to(target.resolve()), name
                archive.extractall(target)
            instructions = (target / f"START-HERE-{experiment_id}.txt").read_text(encoding="utf-8")
            for field in ("question", "finding", "limitations", "outcome"):
                assert record[field] in instructions, (experiment_id, field)
            assert record["reproduction"]["command"] in instructions
            assert "Python 3.9 or later" in instructions
            manifest = target / f"EXPERIMENT-{experiment_id}-CONTENTS.json"
            assert f"python scripts/verify_bundle.py {manifest.name}" in instructions
            checked, problems = verify(manifest)
            assert checked and not problems, (experiment_id, problems)
            members = {item["path"]: item for item in json.loads(manifest.read_text())}
            image_manifest = target / f"EXPERIMENT-{experiment_id}-IMAGE-INPUTS.json"
            images = ({item["path"]: item for item in json.loads(image_manifest.read_text())}
                      if image_manifest.exists() else {})
            for item in record["reproduction"]["inputs"] + record["reproduction"]["outputs"]:
                actual = members.get(item["path"], images.get(item["path"]))
                assert actual and actual["sha256"] == item["sha256"], item["path"]
            assert members[record["reproduction"]["script"]]["sha256"] == record["script_sha256"]
            for name, item in images.items():
                assert name in shared_originals, ('Missing from shared image bundle', experiment_id, name)
                assert item['sha256'] == shared_originals[name]['sha256'], ('Wrong image version', experiment_id, name)
            assert not set(members) & set(images)
            assert (target / f"experiments/records/{experiment_id}/record.json").is_file()
            plan_file = target / f"experiments/records/{experiment_id}/plan.json"
            if plan_file.exists():
                plan = json.loads(plan_file.read_text(encoding="utf-8"))
                results_file = plan_file.with_name("results.json")
                if results_file.exists():
                    result_record = json.loads(results_file.read_text(encoding="utf-8"))
                    if "plan_sha256" in result_record:
                        assert result_record["plan_sha256"] == hashlib.sha256(plan_file.read_bytes()).hexdigest(), experiment_id
                for dependency in plan.get("inputs", []):
                    name = dependency["path"]
                    if name in images:
                        # Original page JPEGs are supplied by the separate image bundle.
                        assert images[name]["sha256"] == dependency["sha256"], (experiment_id, name)
                    else:
                        data = (target / name).read_bytes()
                        assert hashlib.sha256(data).hexdigest() == dependency["sha256"], (experiment_id, name)
            if experiment_id in ("lp2-word-order-reversal", "lp2-prime-openings", "lp2-fibonacci-openings", "lp2-totient-openings", "lp2-trigram-repeats", "prime-distance-reverse-add", "word-sum-corpus-control"):
                for script, args in (("run.py", ["--check"]), ("check.py", [])):
                    result = subprocess.run(
                        [sys.executable, str(target / f"experiments/records/{experiment_id}/{script}"), *args],
                        cwd=target, capture_output=True, text=True, encoding="utf-8", timeout=60)
                    assert result.returncode == 0, (experiment_id, script, result.stdout + result.stderr)
            if experiment_id == "feedback-opening-census":
                for script, args in ((f"experiments/records/{experiment_id}/run.py", ["--check"]),
                                     (f"experiments/suites/{experiment_id}/check.py", [])):
                    result = subprocess.run([sys.executable, str(target / script), *args], cwd=target,
                                            capture_output=True, text=True, encoding="utf-8", timeout=60)
                    assert result.returncode == 0, (experiment_id, script, result.stdout + result.stderr)
        print(f"PASS: selected {len(selected)}/{len(records)} experiment bundles preserve declared files and hashes; "
              "applicable representative runners/checkers pass in isolated extractions.")


if __name__ == "__main__":
    main()
