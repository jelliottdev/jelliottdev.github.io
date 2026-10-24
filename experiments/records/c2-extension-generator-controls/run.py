"""Replay 56 frozen C2-EXT plants with the unchanged source decoder, offline."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE / 'source/liber-primus/analysis/round24/C2-ext-skip-generators'))
import control_ext as source


def load(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def fixtures_check():
    for item in load('source-manifest.json')['files']:
        assert hashlib.sha256((HERE / 'source' / item['path']).read_bytes()).hexdigest() == item['sha256']
    fixtures = load('fixtures.json')
    assert len(fixtures['cases']) == 56
    for row in fixtures['cases']:
        s = row['seed'] - 3301
        assert row['plain'] == source.take_plain(240, s)
        assert row['key'] == source.axis_key(row['axis'].split(':')[0], row['seed'], 3424)
        kw = dict(supp=.83, seed=row['seed'])
        if ':' not in row['axis']:
            cipher, events = source.enc_skip_by_two(row['plain'], row['key'], **kw)
        elif row['axis'].endswith('free_drift'):
            cipher, events = source.enc_free_drift(row['plain'], row['key'], q=.05, **kw)
        else:
            cipher, events = source.enc_drift_at(row['plain'], row['key'], ndrift=10, **kw)
        assert (cipher, events) == (row['cipher'], row['n_events'])
    return fixtures['cases']


def main(check=False):
    fixtures = fixtures_check()
    if check:
        import check as independent
        independent.main()
        print('PASS: exact source bytes and all 56 generated fixtures; saved traces independently checked')
        return
    traces = []
    for row in fixtures:
        result = dict(axis=row['axis'], seed=row['seed'])
        for name, preset in [('beam', source.BEAM), ('dec', source.DB.PRESETS[row['preset']])]:
            decoded = source.DB.beam_decode(row['cipher'], row['key'], sign=-1, o=0, beam_w=400, **preset)
            result[name + '_plain'] = decoded['plain_idx']
            result[name + '_score'] = decoded['score']
        traces.append(result)
        print(row['axis'], row['seed'], flush=True)
    (HERE / 'traces.json').write_text(json.dumps(traces, separators=(',', ':')) + '\n', encoding='utf-8')
    import check as independent
    independent.main()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Verify fixtures and saved traces without rerunning 112 beams')
    main(parser.parse_args().check)
