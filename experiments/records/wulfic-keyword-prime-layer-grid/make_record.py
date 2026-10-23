"""Build declaration and hashes for the corrected, bounded legacy test."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = f'experiments/records/{HERE.name}/'


def hashed(path):
    return {'path': path, 'sha256': hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}


def main():
    d = json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    assert d['candidate_count'] == 224128 and d['page_count'] == 34
    assert d['source_screen_hit_count'] == 0
    assert d['global_max_null_ge_observed'] == 42
    assert abs(d['best']['best_ioc']-1.290220385674931) < 1e-12
    assert d['known_reading_control']['exact_recovery']
    inputs = [BASE+n for n in ('plan.json','plan-initial-frozen.json','input-mapping-amendment.json',
                                'source-gp-hashes.json','keys.json','run.py','check.py','plot.py','make_record.py')]
    inputs += ['data/index.json','data/evidence/known-readings.json']
    inputs += [f'text/lp2-{p:02d}.txt' for p in range(4,38)]
    record = {
        'id': HERE.name, 'status': 'draft',
        'title': 'Keywords paired with prime-derived streams',
        'question': 'Does any source-specified keyword and prime-derived stream combination lift LP2 page text above the archived IoC candidate screen?',
        'reader_question': 'Could a keyword and a prime stream remove two cipher layers?',
        'summary': 'An adapted test of a pinned archived source grid found no setting above its IoC screen on the correctly mapped LP2 pages.',
        'finding': 'Across 224,128 keyword/stream/sign/page settings on LP2-04–37, none scored above the source IoC>1.40 screen. The maximum was 1.2902 on LP2-32. A 515-rune established reading encrypted with one declared setting was recovered exactly and scored 1.7231. In 49 seeded page-wise shuffle controls repeating the full search, 42 reached a maximum at least as high as the LP2 maximum.',
        'limitations': 'This is the exact finite source grid adapted to verified current text, not a replay of the archived script’s old results. Its directory and page-number assumptions were outdated; old page_21–54 means current LP2-04–37. A prior wrong-target exploratory run was discarded and documented. The 515-rune positive control is longer than any target page, so it does not establish equal power on short pages. IoC is not a language detector; 49 shuffles preserve page histograms but do not model every cipher. Other keywords, stream rules, phases, boundaries or layers remain outside scope.',
        'next_steps': 'A related claim should specify both complete key streams and the page boundary/reset rule, then show a full reading that survives a whole-search comparison and a planted control.',
        'outcome': 'not-supported',
        'tags': ['LP2','source adaptation','keyword cipher','prime stream','two layers','index of coincidence'],
        'scope': {
            'pages': [f'lp2-{p:02d}' for p in range(4,38)],
            'artifacts': [BASE+'source-gp-hashes.json',BASE+'input-mapping-amendment.json'],
            'representation': 'Current canonical GP29 rune streams for LP2-04–37, verified length and SHA256 identical to the archived source’s old page_21–54 rune streams. Each page is separate; no word resets.',
            'procedure': 'For each page apply all 16 source numeric keyword arrays, 103 source second streams and four keyword/stream sign pairs modulo29. Score source-normalized IoC; record each page maximum and IoC>1.40 count. Plant a complete known reading and rerun the full selection on 49 seeded within-page shuffles.',
            'parameters': '34 pages ×16 keyword arrays ×103 second streams ×4 sign pairs =224,128 settings. Second streams: 50 prime-minus-one offsets, 50 prime offsets, cumulative prime-minus-one, linear and Fibonacci. Source IoC screen>1.40; 49 page-wise histogram-preserving shuffles, seed20261023.',
            'exclusions': 'LP2 outside pages04–37; keyword phase changes, new words, transpositions, alternate prime orders/indices, feedback, page joins, null skipping, adaptive keys, additional layers and non-IoC language scores.'
        },
        'review': {
            'kind': 'pinned archived-source finite-grid adaptation with corrected page mapping',
            'retested_on': '2026-10-23',
            'reviewer': 'Original/current input streams match for all34 pages by independent nonempty length and SHA256; full grid and all49 whole-search nulls reproducible; scalar checks of all34 selected winners; exact planted known-reading recovery',
            'human_review': 'pending'
        },
        'reproduction': {
            'command': f'python {BASE}check.py && python {BASE}plot.py --check',
            'environment': 'Python3 with NumPy and Numba. The pinned source checkout is needed only to independently regenerate the archived rune hashes; the exact hashes and source link are bundled.',
            'script': BASE+'check.py', 'script_sha256': hashed(BASE+'check.py')['sha256'],
            'inputs': [hashed(p) for p in inputs],
            'outputs': [hashed(BASE+n) for n in ('results.json','comparison.svg')]
        },
        'visuals': [{'path': BASE+'comparison.svg','caption': 'The LP2 search maximum lies below the archived candidate screen. The planted reading crosses it; page-shuffle maxima often exceed the LP2 maximum.'}],
        'sources': [
            {'label':'Pinned archived keyword-plus-stream source','url':'https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/combined_cipher_test.py'},
            {'label':'Upstream warning about archived scripts','url':'https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/README.md'}
        ],
        'related': ['lp2-prime-openings','lp2-totient-openings','wulfic-keyword-quagmire-models']
    }
    (HERE/'record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':
    main()
