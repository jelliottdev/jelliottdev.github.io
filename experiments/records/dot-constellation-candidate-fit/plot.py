"""Saved same-scale overlays; no new fitting, points or candidate selection."""
import argparse
import html
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def build():
    result = json.loads((HERE/'matching-results.json').read_text(encoding='utf-8'))
    target = result['targets'][0]
    candidates = json.loads((HERE/'constellation-candidates.json').read_text(encoding='utf-8'))
    lookup = {r['constellation']: r for r in candidates}
    minima = {r['constellation']: r for r in target['candidate_minima']}
    query = np.asarray(target['query_points_pixels'])
    names = [target['best_witness']['candidate'], 'Ori', 'Aql', 'Boo']
    panels = []
    for name in names:
        row, source = minima[name], lookup[name]
        witness = row['witness']
        fitted = np.asarray(source['gnomonic_xy'])@np.asarray(witness['orthogonal_matrix'])*witness['scale']+witness['translation']
        panels.append({'constellation': name, 'name': source['name'], 'rank': row['rank'],
                       'HRs': [s['HR'] for s in source['stars']],
                       'star_to_query_indices': witness['star_to_query_indices'],
                       'fitted_stars_pixels': fitted.tolist(), 'dots_pixels': query.tolist(),
                       'normalized_rms': row['score'], 'rms_pixels': witness['rms_query_units'],
                       'maximum_pixels': witness['maximum_query_units']})
    visual = {'schema': 'liberpedia-five-dot-star-overlay-v1', 'primary_page': 'lp2-07',
              'note': 'Measured dot centroids and transformed fixed catalogue positions; symbolic markers, no constellation lines.',
              'panels': panels}
    all_points = np.vstack([query, *[np.asarray(p['fitted_stars_pixels']) for p in panels]])
    low, high = all_points.min(axis=0), all_points.max(axis=0)
    scale = min(510/(high[0]-low[0]), 148/(high[1]-low[1]))
    centre = (low+high)/2
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="600" height="1310" viewBox="0 0 600 1310" role="img" aria-labelledby="title description">',
           '<title id="title">Five-star patterns against the five dots</title>',
           '<desc id="description">Four same-scale overlays compare the LP2-07 measured dots with fitted catalogue entries. Volans is closest of 88 fixed patterns, with a 34.9-pixel root-mean-square residual. The named Orion, Aquila and Bootes patterns fit less closely.</desc>',
           '<rect width="600" height="1310" fill="white"/>',
           '<g font-family="Arial,sans-serif" fill="#252b32">',
           '<text x="25" y="37" font-size="26">Five-star patterns against the five dots</text>',
           '<text x="25" y="70" font-size="20">Same scale in every panel · fixed catalogue rule</text>',
           '<circle cx="34" cy="102" r="5" fill="#252b32"/><text x="49" y="109" font-size="20">Measured dots</text>',
           '<circle cx="249" cy="102" r="8" fill="none" stroke="#70777e" stroke-width="1.5"/><text x="265" y="109" font-size="20">Fitted star entries</text>']
    for ordinal, panel in enumerate(panels):
        top = 135+ordinal*250
        out.append(f'<path d="M25 {top}H575" stroke="#dfe2e4"/>')
        name = html.escape(panel['name'])
        out.append(f'<text x="25" y="{top+30}" font-size="23">{name}</text>')
        out.append(f'<text x="25" y="{top+59}" font-size="20">Rank {panel["rank"]} of 88 · RMS miss {panel["rms_pixels"]:.1f} pixels</text>')
        def xy(point):
            return 300+(point[0]-centre[0])*scale, top+155+(point[1]-centre[1])*scale
        for i, point in enumerate(panel['fitted_stars_pixels']):
            star = xy(point)
            dot = xy(query[panel['star_to_query_indices'][i]])
            out.append(f'<path d="M{star[0]:.6f} {star[1]:.6f}L{dot[0]:.6f} {dot[1]:.6f}" stroke="#9ca3a9" stroke-width="1.3" stroke-dasharray="3 3"/>')
            out.append(f'<circle cx="{star[0]:.6f}" cy="{star[1]:.6f}" r="8" fill="white" stroke="#70777e" stroke-width="1.5"/>')
        for point in query:
            dot = xy(point)
            out.append(f'<circle cx="{dot[0]:.6f}" cy="{dot[1]:.6f}" r="5" fill="#252b32"/>')
    best = minima[names[0]]['full_selection_references']
    out += ['<path d="M25 1140H575" stroke="#dfe2e4"/>',
            '<text x="25" y="1172" font-size="22">Other shapes matched at least this closely:</text>',
            f'<text x="25" y="1205" font-size="20">{best["uniform_disk"]["count_at_or_below"]} / 4095 uniform-disk searches</text>',
            f'<text x="25" y="1237" font-size="20">{best["catalogue_sets"]["count_at_or_below"]} / 4095 sampled-catalogue searches</text>',
            '<text x="25" y="1282" font-size="20">A geometric fit does not establish astronomical intent.</text>',
            '</g></svg>']
    return json.dumps(visual, ensure_ascii=False, indent=2)+'\n', '\n'.join(out)+'\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    visual, svg = build()
    for name, value in [('visual-data.json', visual), ('star-overlays.svg', svg)]:
        if args.check:
            assert (HERE/name).read_text(encoding='utf-8') == value, name
        else:
            (HERE/name).write_text(value, encoding='utf-8', newline='\n')
    print('PASS: same-scale overlays use saved measurements and witnesses' if args.check else 'Wrote overlay SVG and native-ready points')
