"""Exact numeric2 Part A source calls only; offline, no Parts B/C."""
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    lp = HERE / 'source/liber-primus'
    sys.path[:0] = [str(lp / 'analysis/campaign18_skip/armada2'),
                   str(lp / 'analysis/campaign18_skip'), str(lp / 'analysis'),
                   str(lp / 'src')]
    import numeric2_skip as source
    import sweep
    from run_stats import load_pages
    from skipdecode import idx_to_trans
    streams = json.loads((HERE / 'streams.json').read_text(encoding='utf8'))
    generated = source.build_fixed_catalog(1172)
    assert [(x['name'], x['key']) for x in streams] == [(n, list(map(int, k))) for n, k in generated]
    pages = load_pages()[:-2]
    assert len(pages) == 55 and max(map(len, pages)) == 277
    for page_id, values in zip(PLAN['page_ids'], pages):
        text = (ROOT / ('text/' + page_id + '.txt')).read_text(encoding='utf8')
        assert source.gp.runes_to_indices(text) == values
    return source, sweep, idx_to_trans, streams, pages


PLAN = json.loads((HERE / 'plan.json').read_text(encoding='utf8'))


def main():
    for item in PLAN['inputs']:
        assert sha(ROOT / item['path']) == item['sha256'], item['path']
    source, sweep, translit, streams, pages = load()
    rows = []
    started = time.perf_counter()
    # Preserve source Part A loop order and exact _score_page gate behavior.
    for stream in streams:
        key = np.asarray(stream['key'], dtype=np.int64)
        for page_id, values in zip(PLAN['page_ids'], pages):
            cipher = np.asarray(values, dtype=np.int64)
            for sign in (-1, 1):
                for atbash in (0, 1):
                    transformed = source._atbash(cipher) if atbash else cipher
                    for offset in range(5):
                        assert offset + 4 * len(cipher) + 8 <= len(key)
                        short = sweep.beam(transformed, key, sign, offset, min(50, len(cipher)), 60)
                        screen_score = source.Q.score_norm(translit(short))
                        row = {'stream': stream['name'], 'page': page_id, 'sign': sign,
                               'atbash': atbash, 'offset': offset, 'screen_score': screen_score,
                               'screen_length': len(short),
                               'screen_sha256': hashlib.sha256(bytes(short)).hexdigest(),
                               'selected_full': screen_score > -6.5}
                        if row['selected_full']:
                            full = sweep.beam(transformed, key, sign, offset, len(cipher), 300)
                            row.update(full_indices=full, full_score=source.Q.score_norm(translit(full)),
                                       full_sha256=hashlib.sha256(bytes(full)).hexdigest())
                            row['source_gate_pass'] = row['full_score'] > -5.5
                        rows.append(row)
        print('Completed', stream['name'], flush=True)
    assert len(rows) == 23100
    (HERE / 'cases.json').write_text(json.dumps(rows, separators=(',', ':')) + '\n', encoding='utf8', newline='\n')
    full = [r for r in rows if r['selected_full']]
    report = {'schema': 'artifact-stream-skip-grid-v1', 'plan_sha256': sha(HERE / 'plan.json'),
              'settings': len(rows), 'named_streams': 21, 'full_confirmations': len(full),
              'source_gate_passes': sum(r['source_gate_pass'] for r in full),
              'best_screen': max(rows, key=lambda r: r['screen_score']),
              'best_full': max(full, key=lambda r: r['full_score']) if full else None,
              'cases_sha256': sha(HERE / 'cases.json'), 'elapsed_seconds': time.perf_counter() - started,
              'limit': 'Selected source score gates, not plaintext validation, global probability or exclusion of numeric keys.'}
    (HERE / 'results.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8', newline='\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
