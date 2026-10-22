"""Measure the exact effect of the eight published reviewed-text corrections.

Standard library only. --check recomputes the saved report and figure. No files are
written unless --output is given; that option refuses to overwrite an existing file.
"""
import argparse
from collections import Counter
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PAGES = ('lp1-10', 'lp2-05', 'lp2-07', 'lp2-11', 'lp2-15', 'lp2-35', 'lp2-37', 'lp2-38')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tokens(text, runes):
    # Match the published word-length census: slash/CR/LF are wraps, while
    # punctuation remains. Apostrophes internal to rune runs do not split one.
    flattened = text.replace('/', '').replace('\r', '').replace('\n', '')
    return re.findall(f'[{re.escape(runes)}]+(?:\'[{re.escape(runes)}]+)*', flattened)


def runes_only(text, runes):
    unknown = {c for c in text if '\u16a0' <= c <= '\u16ff' and c not in runes}
    if unknown:
        raise ValueError('Unknown Runic-block symbol: ' + repr(sorted(unknown)))
    return ''.join(c for c in text if c in runes)


def lengths(items, runes):
    return [sum(c in runes for c in item) for item in items]


def ordered_changes(left, right):
    result = []
    for kind, a, b, c, d in SequenceMatcher(None, left, right, autojunk=False).get_opcodes():
        if kind != 'equal':
            result.append({'operation': kind, 'archived_range': [a, b],
                           'reviewed_range': [c, d],
                           'archived_lengths': left[a:b], 'reviewed_lengths': right[c:d]})
    return result


def ioc_pair_counts(stream):
    counts = Counter(stream)
    return [sum(n*(n-1) for n in counts.values()), len(stream)*(len(stream)-1)]


def report():
    plan_path = HERE / 'plan.json'
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    assert tuple(plan['pages']) == PAGES
    for item in plan['inputs']:
        path = ROOT / item['path']
        if sha(path) != item['sha256']:
            raise ValueError('Plan input changed: ' + item['path'])
    index = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))
    runes = ''.join(item['rune'] for item in index['alphabet'])
    assert len(runes) == len(set(runes)) == 29
    rows = []
    for page_id in PAGES:
        path = ROOT / 'data/pages' / (page_id + '.json')
        page = json.loads(path.read_text(encoding='utf-8'))
        archived, reviewed = page['raw'], page['reviewed_text']
        assert archived != reviewed and page['corrections']
        left, right = runes_only(archived, runes), runes_only(reviewed, runes)
        before_tokens, after_tokens = tokens(archived, runes), tokens(reviewed, runes)
        before, after = lengths(before_tokens, runes), lengths(after_tokens, runes)
        before_bigrams, after_bigrams = Counter(zip(left, left[1:])), Counter(zip(right, right[1:]))
        before_marks = Counter(c for c in archived if c not in runes)
        after_marks = Counter(c for c in reviewed if c not in runes)
        mark_delta = {c: after_marks[c]-before_marks[c] for c in sorted(before_marks | after_marks)
                      if after_marks[c] != before_marks[c]}
        rows.append({
            'page': page_id, 'record_sha256': sha(path),
            'corrections': page['corrections'],
            'rune_sequence_equal': left == right,
            'rune_multiset_equal': Counter(left) == Counter(right),
            'rune_count': len(left), 'archived_rune_sha256': hashlib.sha256(left.encode()).hexdigest(),
            'reviewed_rune_sha256': hashlib.sha256(right.encode()).hexdigest(),
            'whole_page_ioc_archived': ioc_pair_counts(left),
            'whole_page_ioc_reviewed': ioc_pair_counts(right),
            'archived_token_count': len(before), 'reviewed_token_count': len(after),
            'rune_token_sequence_equal': [''.join(c for c in t if c in runes) for t in before_tokens]
                == [''.join(c for c in t if c in runes) for t in after_tokens],
            'non_rune_count_delta': mark_delta,
            'archived_max_token_length': max(before), 'reviewed_max_token_length': max(after),
            'archived_histogram': {str(k): v for k,v in sorted(Counter(before).items())},
            'reviewed_histogram': {str(k): v for k,v in sorted(Counter(after).items())},
            'token_length_changes': ordered_changes(before, after),
            'ordered_bigram_types_changed': len(set(before_bigrams) | set(after_bigrams))
                - sum(before_bigrams[k] == after_bigrams[k] for k in set(before_bigrams) | set(after_bigrams)),
        })
    # Apply only the seven published LP2 reviewed layers to the complete LP2
    # corpus. Leave every other LP2 page exactly as archived.
    corpus = {}
    for mode in ('archived', 'reviewed'):
        pieces = []
        for number in range(56):
            page_id = f'lp2-{number:02d}'
            page = json.loads((ROOT / 'data/pages' / (page_id + '.json')).read_text(encoding='utf-8'))
            pieces.append(page['reviewed_text'] if mode == 'reviewed' and page_id in PAGES else page['raw'])
        stream = ''.join(pieces)
        rune_stream = runes_only(stream, runes)
        values = lengths(tokens(stream, runes), runes)
        corpus[mode] = {'rune_sha256': hashlib.sha256(rune_stream.encode()).hexdigest(),
                        'rune_count': len(rune_stream), 'whole_stream_ioc': ioc_pair_counts(rune_stream),
                        'token_count': len(values), 'max_token_length': max(values),
                        'rune_token_sequence_sha256': hashlib.sha256('\0'.join(''.join(c for c in t if c in runes) for t in tokens(stream, runes)).encode()).hexdigest(),
                        'histogram': {str(k): v for k,v in sorted(Counter(values).items())}}
    assert corpus['archived']['token_count'] == 2896  # Published word-length control.
    assert corpus['archived']['rune_sha256'] == corpus['reviewed']['rune_sha256']
    assert corpus['archived']['whole_stream_ioc'] == corpus['reviewed']['whole_stream_ioc']
    assert corpus['archived']['rune_token_sequence_sha256'] == corpus['reviewed']['rune_token_sequence_sha256']
    assert all(row['rune_sequence_equal'] for row in rows if row['page'].startswith('lp2-'))
    assert not next(row for row in rows if row['page'] == 'lp1-10')['rune_sequence_equal']
    return {'schema': 'liberpedia-transcription-correction-sensitivity-v1',
            'plan_sha256': sha(plan_path), 'scope': 'Eight published reviewed-text layers only; no new image review.',
            'method': 'Use the archived raw and reviewed_text fields of current page records. Apply the same rune-token rule as scripts/rune_word_lengths.py. Compare exact rune streams, whole-stream IoC pair counts, token lengths, and ordered bigrams.',
            'pages': rows, 'lp2_corpus': corpus,
            'limits': 'These effects are conditional on the eight stored corrections and this token rule. They do not validate the corrections against the original images or measure unrecorded disputed marks.'}


def figure(result):
    rows = result['pages']
    width, height = 360, 618
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
             '<title id="title">Eight reviewed corrections and the measures they change</title>',
             '<desc id="desc">For each page, the chart shows the non-rune marks added or removed and whether ordered runes or rune tokens changed. Seven LP2 pages have mark edits but unchanged rune and token streams. LP1-10 changes rune order, leaving token length counts unchanged.</desc>',
             '<rect width="360" height="618" fill="#faf9f5"/>',
             '<g font-family="Arial,sans-serif" fill="#263b45">',
             '<text x="16" y="31" font-size="18">What the corrections change</text>',
             '<text x="16" y="54" font-size="13">The original images were not rechecked here</text>']
    for i, row in enumerate(rows):
        y = 79 + i*63
        marks = ', '.join(f'{c if c not in chr(10)+chr(13) else "line break"} {n:+d}' for c,n in row['non_rune_count_delta'].items()) or 'none'
        lines += [f'<path d="M16 {y+50}H344" stroke="#e3e1da"/>',
                  f'<text x="16" y="{y+13}" font-size="16" font-weight="bold">{row["page"].upper()}</text>',
                  f'<text x="151" y="{y+13}" font-size="14">Mark edits: {marks.replace("&", "&amp;").replace("<", "&lt;")}</text>',
                  f'<text x="16" y="{y+37}" font-size="14" fill="{"#a74e37" if not row["rune_sequence_equal"] else "#315f73"}">Runes: {"changed" if not row["rune_sequence_equal"] else "same"}</text>',
                  f'<text x="180" y="{y+37}" font-size="14" fill="{"#315f73" if row["rune_token_sequence_equal"] else "#a74e37"}">Tokens: {"same" if row["rune_token_sequence_equal"] else "changed"}</text>']
    lines += ['<text x="16" y="595" font-size="12">Tokens follow the published word-length rule;</text>',
              '<text x="16" y="611" font-size="12">other delimiter rules can differ.</text>', '</g></svg>']
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true')
    group.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = report()
    if args.check:
        if result != json.loads((HERE / 'results.json').read_text(encoding='utf-8')):
            raise SystemExit('Recorded result differs')
        if figure(result) != (HERE / 'correction-effects.svg').read_text(encoding='utf-8'):
            raise SystemExit('Recorded figure differs')
        print('PASS: eight page comparisons, complete LP2 corpus, and figure reproduce')
    elif args.output:
        with args.output.open('x', encoding='utf-8', newline='\n') as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
    else:
        print(json.dumps({'pages': [{k: r[k] for k in ('page', 'archived_token_count', 'reviewed_token_count', 'ordered_bigram_types_changed')} for r in result['pages']], 'lp2_corpus': result['lp2_corpus']}, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
