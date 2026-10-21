"""Render all audited corpus ranks. No selection, inference, or recalculation of ranks."""
import argparse
import hashlib
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'experiments/plans/corpus-prefix-comparison.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def label(measure):
    if measure.startswith('length_'):
        return 'Length ' + measure[7:].replace('_plus', '+')
    return {'sample_std': 'Standard deviation', 'sample_variance': 'Variance',
            'percentile_25': 'Lower quartile', 'percentile_75': 'Upper quartile',
            'min': 'Minimum', 'max': 'Maximum'}.get(measure, measure.title())


def validate_rows(comparison, plan):
    assert list(comparison['comparisons']) == plan['weighting']
    for rows in comparison['comparisons'].values():
        assert [r['measure'] for r in rows] == plan['measures']
        totals = set()
        for r in rows:
            fields = ['reference_count', 'below', 'equal', 'above',
                      'inclusive_left_numerator', 'inclusive_right_numerator']
            assert all(type(r[k]) is int and r[k] >= 0 for k in fields)
            n = r['reference_count']; totals.add(n)
            assert n > 0 and r['below'] + r['equal'] + r['above'] == n
            assert r['inclusive_left_numerator'] == r['below'] + r['equal']
            assert r['inclusive_right_numerator'] == r['above'] + r['equal']
            assert r['comparison_scale'] == ('variance' if r['measure'] == 'sample_std' else r['measure'])
            value = r['target_comparison_value']
            assert type(value['numerator']) is int and value['numerator'] >= 0
            assert type(value['denominator']) is int and value['denominator'] > 0
        assert len(totals) == 1


def render(comparison, plan):
    validate_rows(comparison, plan)
    count = len(plan['measures']); panel_height = 85 + 27 * count
    height = 115 + panel_height * len(plan['weighting'])
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 {height}" role="img" aria-labelledby="title desc">',
           '<title id="title">Manuscript positions in the audited corpus</title>',
           '<desc id="desc">All 23 measures under path weighting and distinct-blob weighting. Each bar partitions reference prefixes into values below, equal to, and above the manuscript. These are descriptive ranks, not probabilities.</desc>',
           f'<rect width="380" height="{height}" fill="white"/>',
           '<style>text{font:12px Arial,sans-serif;fill:#253d49}</style>',
           '<text x="12" y="23" style="font-size:16px;font-weight:bold">Where the manuscript falls</text>',
           '<text x="12" y="44">Share of reference prefixes, by measure</text>']
    for i,(name,color) in enumerate([('Below','#315f76'),('Equal','#b4c8d2'),('Above','#e6e9eb')]):
        x = 12 + i*115
        svg += [f'<rect x="{x}" y="59" width="12" height="12" fill="{color}"/>',
                f'<text x="{x+18}" y="70">{name}</text>']
    md = ['## Complete corpus comparison', '',
          'Every planned measure is shown under both weighting rules. Bars partition reference prefixes by whether their value is below, equal to, or above the manuscript value. They do not show probabilities of a language or cipher.', '',
          'The two inclusive fractions both contain ties: they can sum to more than one. Distinct Git blobs remove byte-identical duplicates only; editions, translations and overlapping works may remain. Manuscript values are exact fractions; length-bin values are proportions. Standard deviation is shown as a square root, while its ranks use exact variance ordering, which preserves all ties.', '']
    for panel,(weight,rows) in enumerate(comparison['comparisons'].items()):
        top = 100 + panel*panel_height
        heading = 'Every eligible path' if weight == 'eligible path' else 'Distinct eligible Git blobs'
        svg.append(f'<text x="12" y="{top}" style="font-weight:bold">{heading} · n = {rows[0]["reference_count"]:,}</text>')
        md += ['### '+heading, '', '| Measure | Manuscript value | Below | Equal | Above | At or below | At or above |',
               '| --- | --- | ---: | ---: | ---: | --- | --- |']
        for i,r in enumerate(rows):
            y = top + 28 + i*27; n = r['reference_count']; x = 145
            svg.append(f'<text x="12" y="{y+11}">{html.escape(label(r["measure"]))}</text>')
            for key,color in [('below','#315f76'),('equal','#b4c8d2'),('above','#e6e9eb')]:
                width = 220*r[key]/n
                svg.append(f'<rect x="{x:.6f}" y="{y}" width="{width:.6f}" height="15" fill="{color}"><title>{key}: {r[key]} / {n}</title></rect>')
                x += width
            target = r['target_comparison_value']
            value = str(target['numerator']) if target['denominator'] == 1 else f'{target["numerator"]}/{target["denominator"]}'
            if r['measure'] == 'sample_std':
                value = f'√({value})'
            md.append(f'| {label(r["measure"])} | {value} | {r["below"]} | {r["equal"]} | {r["above"]} | {r["inclusive_left_numerator"]}/{n} | {r["inclusive_right_numerator"]}/{n} |')
        axis = top + 28 + count*27
        for x,text in [(145,'0%'),(255,'50%'),(365,'100%')]:
            svg.append(f'<text x="{x}" y="{axis}" text-anchor="middle">{text}</text>')
        md.append('')
    svg += [f'<text x="12" y="{height-12}">Fixed-corpus positions · not calibrated p-values</text>', '</svg>']
    return '\n'.join(svg)+'\n', '\n'.join(md)+'\n'


def verified_inputs(census, source_receipt, comparison_path, comparison_receipt):
    comparison = json.loads(comparison_path.read_bytes())
    receipt = json.loads(comparison_receipt.read_bytes())
    source = json.loads(source_receipt.read_bytes())
    plan = json.loads(PLAN.read_bytes())
    assert comparison['plan_sha256'] == digest(PLAN)
    assert comparison['script_sha256'] == digest(ROOT/'scripts/compare_corpus_prefixes.py')
    assert receipt['checker_sha256'] == digest(ROOT/'scripts/check_corpus_comparison.py')
    assert source['checker_sha256'] == digest(ROOT/'scripts/check_corpus_prefixes.py')
    assert receipt['comparison_sha256'] == digest(comparison_path)
    assert comparison['census_sha256'] == receipt['census_sha256'] == source['report_sha256'] == digest(census)
    assert comparison['source_audit_receipt_sha256'] == receipt['source_audit_receipt_sha256'] == digest(source_receipt)
    assert receipt['measure_rows_checked'] == 46 and source['entries_checked'] == 25906
    validate_rows(comparison, plan)
    assert receipt['eligible_paths'] == comparison['comparisons']['eligible path'][0]['reference_count']
    assert receipt['eligible_blobs'] == comparison['comparisons']['distinct eligible Git blob'][0]['reference_count']
    return comparison, plan


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('census', 'source_receipt', 'comparison', 'comparison_receipt'):
        parser.add_argument(name, type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output directory already exists; choose a new path')
    comparison, plan = verified_inputs(args.census, args.source_receipt, args.comparison, args.comparison_receipt)
    svg, md = render(comparison, plan)
    args.output.mkdir(parents=True)
    (args.output/'comparison.svg').write_text(svg, encoding='utf-8', newline='\n')
    (args.output/'comparison.md').write_text(md, encoding='utf-8', newline='\n')
    print('Rendered all 46 audited rows; no inferential claims added')
