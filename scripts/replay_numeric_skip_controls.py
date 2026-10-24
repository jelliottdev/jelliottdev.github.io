"""Replay all frozen numeric skip plants using only one extracted record bundle.

The audited probe, frozen plan and expected results are never changed. Its
generator loader is replaced by frozen key arrays. Only dependencies used by
the shared encoder/decoder are checked here; numeric generators are not run.
"""
from __future__ import annotations
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def compare(actual, expected, path='result'):
    if isinstance(expected, dict):
        assert set(actual) == set(expected), path
        for key in expected:
            if key in {'elapsed_seconds', 'screen_seconds', 'full_seconds'}:
                continue
            compare(actual[key], expected[key], path + '.' + key)
    elif isinstance(expected, list):
        assert isinstance(actual, list) and len(actual) == len(expected), path
        for index, (left, right) in enumerate(zip(actual, expected)):
            compare(left, right, f'{path}[{index}]')
    elif isinstance(expected, float) and 'score' in path.rsplit('.', 1)[-1]:
        assert math.isclose(actual, expected, rel_tol=0, abs_tol=2e-12), (path, actual, expected)
    else:
        assert actual == expected and type(actual) is type(expected), (path, actual, expected)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', type=Path, required=True, help='Extracted numeric or artifact record directory')
    args = parser.parse_args()
    record = args.record.resolve()
    control = next((record / name for name in ('controls', 'control') if (record / name / 'probe.py').is_file()), None)
    assert control is not None, 'Missing frozen control probe'
    source = record / 'source/liber-primus'
    plan_path = control / 'plan-frozen.json'
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    expected = json.loads((control / 'control-results.json').read_text(encoding='utf-8'))
    assert digest(control / 'probe.py') == expected['probe_sha256'], 'Audited probe hash differs'
    assert digest(plan_path) == expected['plan_sha256'], 'Frozen plan hash differs'
    for relative, wanted in plan['local_hashes'].items():
        assert digest(control / relative) == wanted, relative
    # The probe's original validation also mentions generators and manuscript
    # inputs. These are not dependencies of this array-based control replay.
    used = {'analysis/campaign18_skip/sweep.py', 'analysis/campaign18_skip/skipdecode.py',
            'analysis/run_stats.py', 'src/lp/gematria.py', 'src/lp/score.py',
            'data/english_quadgrams.txt', 'data/keys/solved_plaintext.txt',
            'data/keys/self_reliance.txt'}
    for relative in used:
        assert digest(source / relative) == plan['source_hashes'][relative], relative
    assert not (source / 'data/keys/campaign12/walden.txt').exists(), 'Optional unused source setup differs'
    frozen = json.loads((control / 'streams.json').read_text(encoding='utf-8'))
    streams = [(item['branch'], item['name'], item['key']) for item in frozen]
    assert len(streams) == 54 and sum(br == 'numeric' for br, _, _ in streams) == 33
    assert all(len(key) == (1176 if br == 'numeric' else 1172) for br, _, key in streams)
    spec = importlib.util.spec_from_file_location('frozen_numeric_control_probe', control / 'probe.py')
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    probe.HERE = control
    probe.SRC = source
    sys.path[:0] = [str(source / 'analysis/campaign18_skip'), str(source / 'analysis'), str(source / 'src')]
    import skipdecode
    import sweep
    probe.load = lambda: (None, None, skipdecode, sweep, streams)
    # Keep the original probe's local-input and used-source hash assertions.
    # Filter only its in-memory dependency map, never the frozen plan bytes.
    def portable_loads(text, *positional, **keywords):
        value = json.loads(text, *positional, **keywords)
        if isinstance(value, dict) and 'source_hashes' in value and 'local_hashes' in value:
            assert value == plan
            value['source_hashes'] = {key: value['source_hashes'][key] for key in used}
        return value
    probe.json = SimpleNamespace(loads=portable_loads)
    captured = []
    def capture(path, value):
        assert path == control / 'control-results.json'
        captured.append(value)
    probe.write = capture
    before = {path: digest(path) for path in control.iterdir() if path.is_file()}
    started = time.perf_counter()
    with contextlib.redirect_stdout(io.StringIO()):
        probe.probe()
    assert len(captured) == 1
    compare(captured[0], expected)
    assert len(captured[0]['rows']) == 1080
    assert all(digest(path) == wanted for path, wanted in before.items()), 'Frozen control files changed'
    print(f'PASS: all 1,080 control rows match; exact skips, hashes, gates and recovery flags; '
          f'score tolerance 2e-12; only timing fields ignored. '
          f'Used-source hashes: {len(used)}. No source cache or expected writes. '
          f'Elapsed {time.perf_counter() - started:.2f}s.')

if __name__ == '__main__':
    main()
