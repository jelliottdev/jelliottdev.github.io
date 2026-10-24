"""Replay all frozen synthetic controls without overwriting the original gate."""
import contextlib
import io
import json
from pathlib import Path

import preflight_matching
from execute_matching import close, verify

HERE = Path(__file__).resolve().parent


def without_timing(value):
    timing = {'elapsed_seconds', 'mean_seconds', 'maximum_seconds',
              'projected8190_reference_queries_at_mean_seconds'}
    if isinstance(value, dict):
        return {k: without_timing(v) for k, v in value.items() if k not in timing}
    if isinstance(value, list):
        return [without_timing(v) for v in value]
    return value


def main():
    verify()
    reports = []
    old_write = preflight_matching.write
    preflight_matching.write = lambda path, report: reports.append((path, report))
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            preflight_matching.main()
    finally:
        preflight_matching.write = old_write
    assert len(reports) == 1 and reports[0][0] == HERE/'pretarget-gate.json'
    expected = json.loads((HERE/'pretarget-gate.json').read_text(encoding='utf-8'))
    close(without_timing(reports[0][1]), without_timing(expected))
    print('PASS: 96 mathematical fixtures, 88 exact plants, 1408 noisy plants; all outcomes match; no expected files written')


if __name__ == '__main__':
    main()
