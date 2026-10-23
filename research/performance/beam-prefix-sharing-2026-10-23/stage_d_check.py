"""Read-only checks for the frozen actual-LP2 Stage D addendum."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from stage_d_validate import H, load_inputs, prepare


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    inputs = load_inputs()  # Verifies pinned source/helper and full LP2 arrays.
    plan = inputs[0]
    plan_hash = sha(H / 'stage-d-plan.json')
    parity = json.loads((H / 'stage-d-parity.json').read_text(encoding='utf-8'))
    memory = json.loads((H / 'stage-d-memory.json').read_text(encoding='utf-8'))
    assert parity['plan_sha256'] == memory['plan_sha256'] == plan_hash
    assert len(parity['rows']) == len(plan['arms']) == 2
    compared = ('score', 'beam_score', 'ptr_end', 'runes', 'plain_sha256',
                'translit_sha256', 'key_reads', 'native_key_length',
                'padding_branch_taken', 'padded_zero_read')
    for row, stage in zip(parity['rows'], 'AB'):
        assert row['stage'] == stage
        _, _, cipher, key, _ = prepare(stage, inputs)  # Verifies stage receipt and native key.
        assert len(cipher) == row['source']['runes'] == row['fast']['runes']
        assert len(key) == row['source']['native_key_length']
        assert row['exact_all_return_fields'] is True
        assert row['exact_key_access'] is True
        assert all(row['source'][field] == row['fast'][field] for field in compared)
        assert row['source']['key_reads']['padded_read_count'] == 0
    assert {row['implementation'] for row in memory['rows']} == {'source', 'fast'}
    arm_a = parity['rows'][0]['source']
    for row in memory['rows']:
        assert all(row[field] == arm_a[field] for field in compared)
        assert row['rss_peak'] >= row['rss_baseline'] > 0
        assert row['rss_peak_delta'] == row['rss_peak'] - row['rss_baseline']
    print('PASS Stage D pinned dependencies, actual input/key hashes, two exact parity receipts, RSS receipt')


if __name__ == '__main__':
    main()
