"""Verify the complete saved grid and source-input rune identities."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from run import ROOT, HERE, corpus, full_key_arrays, streams, scalar_score, execute


def main():
    saved = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    assert saved == execute(), 'full grid or shuffle control changed'
    source = json.loads((HERE / 'source-gp-hashes.json').read_text(encoding='utf-8'))
    alphabet = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']
    runes = {x['rune'] for x in alphabet}
    for p in range(4, 38):
        text = (ROOT / f'text/lp2-{p:02d}.txt').read_text(encoding='utf-8')
        seq = ''.join(ch for ch in text if ch in runes)
        witness = source['pages'][f'lp2-{p:02d}']
        assert seq and witness['legacy_page'] == p+17
        assert hashlib.sha256(seq.encode('utf-8')).hexdigest() == witness['source_gp_sha256']
        assert len(seq) == witness['runes']
    pages, _ = corpus()
    key_names, keys = full_key_arrays(515)
    stream_names, secondary = streams(515)
    lookup = {p: c for p, c in pages}
    # A second scalar implementation checks each page winner, not merely a
    # small source-like example. This also verifies numeric key/stream labels.
    for row in saved['pages']:
        cipher = lookup[int(row['page'][-2:])]
        k = keys[key_names.index(row['best_keyword'])]
        s = secondary[stream_names.index(row['best_stream'])]
        ko = ('sub', 'add').index(row['best_keyword_sign'])
        so = ('sub', 'add').index(row['best_stream_sign'])
        assert abs(scalar_score(cipher, k, s, ko, so) - row['best_ioc']) < 1e-12
    assert saved['candidate_count'] == 34*16*103*4 == 224128
    assert saved['known_reading_control']['exact_recovery']
    assert saved['known_reading_control']['passes_source_screen']
    print('PASS: 34 source/site rune identities, 224,128 grid cells, 49 full-search shuffles, scalar winners and known-reading control')


if __name__ == '__main__':
    main()
