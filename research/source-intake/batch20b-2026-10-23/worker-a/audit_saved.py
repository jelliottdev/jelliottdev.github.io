"""Independent arithmetic check of pinned C2/L6 saved rows; no pad replay."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import subprocess

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SOURCE = REPO.parent / 'source-cache' / 'dukotah-cicada3301'
REV = 'f08b20b632d91209ddbaa747e8e2f23df0c78ba1'
A = 'liber-primus/analysis/'


def blob(path):
    return subprocess.check_output(['git', '-C', str(SOURCE), 'show', f'{REV}:{path}'])


def doc(path):
    return json.loads(blob(path))


def receipt(path):
    return {'path': path, 'sha256': hashlib.sha256(blob(path)).hexdigest()}


pref = A + 'round19/C2/out_prefilter_register_power.json'
pd = doc(pref)
assert len(pd['rows']) == 300
assert pd['n_trials'] == 30
assert len(set((r['register'], r['trial']) for r in pd['rows'])) == 300
summary = {}
up = A + 'round19/C2/out_prefilter_union.json'
ud = doc(up)
for reg in pd['summary']:
    rows = [r for r in pd['rows'] if r['register'] == reg]
    assert len(rows) == 30
    rr = {'n': 30, 'n_offsets': 9_999_976}
    for metric in ('tri', 'ioc', 'maxc', 'ndist'):
        ranks = [r['rank_' + metric] for r in rows if r['rank_' + metric] is not None]
        rr['survived_' + metric] = len(ranks)
        rr['survival_' + metric] = len(ranks) / 30
        rr['survival40_' + metric] = sum(r['surv40_' + metric] for r in rows) / 30
        rr['median_rank_' + metric] = statistics.median(ranks) if ranks else None
        for r in rows:
            assert r['surv_' + metric] == (r['rank_' + metric] is not None)
            assert r['surv40_' + metric] == (r['rank_' + metric] is not None and r['rank_' + metric] < 40)
    assert rr == pd['summary'][reg], reg
    tri = sum(r['surv_tri'] for r in rows) / 30
    lang = sum(r['surv_ioc'] or r['surv_maxc'] or r['surv_ndist'] for r in rows) / 30
    union = sum(r['surv_tri'] or r['surv_ioc'] or r['surv_maxc'] or r['surv_ndist'] for r in rows) / 30
    assert ud[reg]['tri'] == tri
    assert ud[reg]['any_langagnostic'] == lang
    assert ud[reg]['union'] == union
    summary[reg] = rr

ocp = A + 'round19/C2/out_offset_coverage.json'
od = doc(ocp)
off = od['aggregate']['derived_branch']
assert off['fraction_of_derived_decodes_at_nonzero_offset'] == off['decodes_run_at_any_NONZERO_key_offset'] / off['total_decodes_all_sweeps']
assert off['fraction_of_axis_2pow20_before_round18'] == off['distinct_key_offsets_ever_tested_before_round18'] / (1 << 20)

spacep = A + 'round19/C2/out_marsaglia_space.json'
sd = doc(spacep)
spb = [1, 1, 1, 1, 1, 2]
per_pad = sum(10_000_000 * n - 24 for n in spb) * 2 * 2
iso = sum(634_124_288 * n - 24 for n in spb) * 2 * 2
assert per_pad * 63 == sd['offsets_all_63_pads']
assert iso == sd['offsets_whole_iso_as_one_pad']
assert sd['units_pads'] == 63 * 6 * 2

a1p = A + 'round18/L6-offset-marsaglia/out/results_A1.json'
a2p = A + 'round18/L6-offset-marsaglia/out/results_A2.json'
a1, a2 = doc(a1p), doc(a2p)
assert (a1['units_done'], a1['units_total'], a1['n_offsets_scanned']) == (220, 220, 220 * (1 << 20))
assert (a2['units_done'], a2['units_total'], a2['n_offsets_scanned']) == (508, 3024, 508 * 2 * (1 << 18))

out = {
    'schema': 'liberpedia-batch20b-worker-a-saved-check-v1',
    'source_revision': REV,
    'scope': 'Independent arithmetic from source-saved rows only; not a rerun of pad scanning, decoder, or checksum verification.',
    'prefilter_rows': 300,
    'registers': {k: {m: v for m, v in vals.items() if m in ('survived_tri', 'survived_ioc', 'survived_maxc', 'survived_ndist')} for k, vals in summary.items()},
    'offset_accounting': {k: off[k] for k in ('total_decodes_all_sweeps', 'decodes_run_at_any_NONZERO_key_offset', 'distinct_key_offsets_ever_tested_before_round18', 'fraction_of_axis_2pow20_before_round18')},
    'marsaglia_analytic_offsets': {'pads': per_pad * 63, 'iso': iso},
    'a1': {'units': 220, 'offsets': a1['n_offsets_scanned']},
    'a2': {'units': 508, 'total': 3024, 'offsets': a2['n_offsets_scanned']},
    'inputs': [receipt(p) for p in (pref, up, ocp, spacep, a1p, a2p)],
}
(HERE / 'saved-check.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8', newline='\n')
print('PASS: 300 prefilter rows, ten summaries/unions, offset fractions, pad-space arithmetic, A1/A2 saved coverage')
