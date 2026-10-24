"""Independently count rune recovery, score paths, and test eight source gates."""
import hashlib
import json
import math
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent


def load(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def main():
    # Read alphabet constants without importing the decoder or scorer.
    namespace = {}
    exec((HERE / 'source/liber-primus/src/lp/gematria.py').read_text(encoding='utf-8'), namespace)
    trans = namespace['IDX_TO_TRANS']
    counts = {}
    for line in (HERE / 'source/liber-primus/data/english_quadgrams.txt').read_text().splitlines():
        word, count = line.split(); counts[word] = int(count)
    total = sum(counts.values()); logtotal = math.log10(total)
    logs = {word: math.log10(count) - logtotal for word, count in counts.items()}
    floor = math.log10(.01) - logtotal
    fixtures = load('fixtures.json')['cases']; traces = load('traces.json')
    assert len(traces) == len(fixtures) == 56
    source = load('source-control.json'); grouped = {}
    assert len({(r['axis'], r['seed']) for r in traces}) == 56
    for fixture, trace in zip(fixtures, traces):
        axis, seed = fixture['axis'], fixture['seed']
        assert (trace['axis'], trace['seed']) == (axis, seed)
        row = next(r for r in source['axes'][axis]['rows'] if r['seed'] == seed)
        item = {'seed': seed}
        for name in ('beam', 'dec'):
            plain = trace[name + '_plain']; assert len(plain) == 240
            assert all(type(x) is int and 0 <= x < 29 for x in plain)
            recovery = sum(a == b for a, b in zip(plain, fixture['plain'])) / 240
            assert recovery == row[name + '_rec']
            text = ''.join(trans[x] for x in plain).upper()
            score = sum(logs.get(text[i:i+4], floor) for i in range(len(text)-3)) / (len(text)-3)
            assert math.isclose(score, trace[name + '_score'], rel_tol=0, abs_tol=1e-12)
            assert trace[name + '_score'] == row[name + '_score']
            item[name + '_rec'] = recovery
        assert fixture['n_events'] == row['n_events']
        doublets = 100 * sum(a == b for a,b in zip(fixture['cipher'],fixture['cipher'][1:])) / 239
        assert math.isclose(doublets, row['ct_doublet_pct'], abs_tol=1e-14)
        grouped.setdefault(axis, []).append(item)
    summary = []
    for axis, rows in grouped.items():
        assert [r['seed'] for r in rows] == list(range(3301, 3308))
        dec = statistics.median(r['dec_rec'] for r in rows)
        beam = statistics.median(r['beam_rec'] for r in rows)
        assert dec == source['axes'][axis]['dec_median_rec']
        assert beam == source['axes'][axis]['beam_median_rec']
        gate = dec >= .9 and beam < .9
        assert gate == source['axes'][axis]['control_validated']
        summary.append(dict(axis=axis, modeled_median=dec, baseline_median=beam,
                            modeled_min=min(r['dec_rec'] for r in rows), passed=gate))
    result = dict(source_revision='f08b20b632d91209ddbaa747e8e2f23df0c78ba1',
                  plants=56, decodes=112, summaries=summary, all_gates=all(r['passed'] for r in summary))
    path = HERE / 'results.json'
    if path.exists(): assert load('results.json') == result
    else: path.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print('PASS: 112 replay scores/recovery counts exactly match source; independent path scores within 1e-12; eight gates recounted')


if __name__ == '__main__':
    main()
