"""Census fixed GP targets in a pinned, locally preserved word corpus."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PLAN = HERE / 'plan.json'
RESULTS = HERE / 'results.json'
FIGURE = HERE / 'candidate-space.svg'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')


def count(plan):
    for item in plan['inputs']:
        path = ROOT / item['path']
        if digest(path) != item['sha256']:
            raise ValueError('Input changed: ' + item['path'])
    manifest = json.loads((ROOT / plan['manifest']).read_text(encoding='utf-8'))
    if manifest['revision'] != plan['corpus_revision']:
        raise ValueError('Corpus revision changed')
    alphabet = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']
    values = {row['rune']: row['prime'] for row in alphabet}
    # The preserved corpus uses ᛂ for J. The manuscript alphabet uses ᛄ.
    # They have the same 37 value, but the glyph mismatch is disclosed.
    values[plan['source_j_rune']] = plan['source_j_prime']
    hist = defaultdict(Counter)
    selected = defaultdict(list)
    word_seen = set()
    rows = 0
    alias_rows = 0
    flags = Counter()
    for item in manifest['files']:
        path = ROOT / 'experiments/records/word-sum-corpus-control/source' / item['path']
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('Corpus file changed: ' + item['path'])
        for word, source_count, flag, runes, printed_sum in csv.reader(data.decode('utf-8').splitlines()):
            if word in word_seen:
                raise ValueError('Duplicate word: ' + word)
            word_seen.add(word)
            if not runes or any(rune not in values for rune in runes):
                raise ValueError('Unmapped rune in: ' + word)
            computed = sum(values[rune] for rune in runes)
            if computed != int(printed_sum):
                raise ValueError('GP mismatch: ' + word)
            length = len(runes)
            hist[length][computed] += 1
            flags[flag] += 1
            rows += 1
            alias_rows += plan['source_j_rune'] in runes
            if computed in plan['target_sums']:
                selected[computed].append({'word': word, 'rune_length': length,
                                           'source_count': int(source_count), 'file': item['path']})
    slots = []
    for slot in plan['phrase_slots']:
        candidates = [row for row in selected[slot['gp_sum']]
                      if row['rune_length'] == slot['rune_length']]
        words = {row['word'] for row in candidates}
        slots.append({**slot, 'candidate_count': len(candidates),
                      'selected_word_in_corpus': slot['selected_word'].lower() in words})
    product = 1
    for slot in slots:
        product *= slot['candidate_count']
    first, second, third, fourth = (slot['candidate_count'] for slot in slots)
    if slots[0]['gp_sum'] != slots[3]['gp_sum'] or slots[0]['rune_length'] != slots[3]['rune_length']:
        raise ValueError('Distinct-pair count assumes matching first and last slots')
    without_repeating_131_word = first * second * third * (fourth - 1)
    return {
        'schema': 'liberpedia-word-sum-corpus-control-v1',
        'plan_sha256': digest(PLAN), 'source_revision': manifest['revision'],
        'source_files': len(manifest['files']), 'source_rows': rows,
        'unique_words': len(word_seen), 'source_j_alias_rows': alias_rows,
        'source_flag_counts': dict(sorted(flags.items())),
        'gp_sum_mismatches': 0,
        'slots': slots,
        'ordered_slot_combinations': product,
        'ordered_combinations_with_distinct_131_words': without_repeating_131_word,
        'target_matches': {str(total): sorted(selected[total], key=lambda row: (row['rune_length'], row['word']))
                           for total in plan['target_sums']},
        'count_by_rune_length_and_gp_sum': {str(length): {str(total): count for total, count in sorted(totals.items())}
                                            for length, totals in sorted(hist.items())},
        'scope_note': 'Counts candidate words and ordered slot combinations, not grammatical sentences or cipher decryptions. Source count and flag fields are preserved but not interpreted as independent evidence.'
    }


def figure(report):
    panels = [(4, 151), (5, 131), (7, 151)]
    width, height = 960, 690
    left, right, plot_width = 82, 920, 838
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
             '<title id="title">Word candidates by rune length and GP sum</title>',
             '<desc id="desc">Three corpus histograms for four, five and seven rune words, with selected target totals highlighted.</desc>',
             '<rect width="960" height="690" fill="#fffdf8"/>',
             '<text x="54" y="38" font-family="Georgia,serif" font-size="24" fill="#20282d">How many words fit a fixed total?</text>',
             '<text x="54" y="66" font-family="Arial,sans-serif" font-size="13" fill="#4f5a61">Pinned 138,466-row crib corpus · each bar is one GP total from 80 to 220</text>']
    for index, (length, mark) in enumerate(panels):
        top = 104 + index * 185
        bottom = top + 125
        values = report['count_by_rune_length_and_gp_sum'][str(length)]
        vmax = max(values.get(str(total), 0) for total in range(80, 221))
        parts.append(f'<text x="54" y="{top-9}" font-family="Arial,sans-serif" font-size="15" font-weight="700" fill="#20282d">{length} runes</text>')
        parts.append(f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#aeb7b9"/>')
        for total in range(80, 221):
            count = values.get(str(total), 0)
            if not count:
                continue
            x = left + (total - 80) * (plot_width / 141)
            bar_height = count / vmax * 107
            color = '#9aaab0' if total != mark else '#b04b37'
            parts.append(f'<rect x="{x:.2f}" y="{bottom-bar_height:.2f}" width="4.6" height="{bar_height:.2f}" fill="{color}"/>')
        marker_x = left + (mark - 80) * (plot_width / 141) + 2.3
        marker_count = values.get(str(mark), 0)
        parts.append(f'<text x="{marker_x:.2f}" y="{top+4}" text-anchor="middle" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="#923923">{escape(str(mark))}: {marker_count} words</text>')
        for tick in (80, 120, 160, 200, 220):
            x = left + (tick - 80) * (plot_width / 141)
            parts.append(f'<text x="{x:.2f}" y="{bottom+18}" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" fill="#58646b">{tick}</text>')
    parts.append('<text x="500" y="671" text-anchor="middle" font-family="Arial,sans-serif" font-size="12" fill="#4f5a61">GP total · display interval only; all totals remain in the downloadable JSON</text></svg>')
    return ('\n'.join(parts) + '\n').encode('utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    result = count(plan)
    result_bytes = canonical(result)
    figure_bytes = figure(result)
    if args.check:
        if RESULTS.read_bytes() != result_bytes or FIGURE.read_bytes() != figure_bytes:
            raise SystemExit('Saved result or figure differs from the pinned corpus replay')
        print('PASS: corpus census and visualization reproduce saved bytes')
    else:
        RESULTS.write_bytes(result_bytes)
        FIGURE.write_bytes(figure_bytes)
        print(f"{result['source_rows']} words; {result['ordered_slot_combinations']} ordered slot combinations")


if __name__ == '__main__':
    main()
