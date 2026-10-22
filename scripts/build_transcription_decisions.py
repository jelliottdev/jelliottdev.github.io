"""Publish exact locations for reviewed edits and unreviewed page-edge candidates."""
from collections import defaultdict
from hashlib import sha256
from html import escape
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'exports/transcription-decisions.json'
ARTICLE = ROOT / 'articles/transcription-decisions.html'


def digest(data):
    return sha256(data).hexdigest()


def line_column(raw, offset):
    prefix = raw[:offset]
    return prefix.count('\n') + 1, len(prefix.rsplit('\n', 1)[-1]) + 1


def report():
    index_bytes = (ROOT / 'data/index.json').read_bytes()
    alphabet = {row['rune'] for row in json.loads(index_bytes)['alphabet']}
    locations = []
    reviewed_pages = []
    for summary in json.loads(index_bytes)['pages']:
        page_id = summary['id']
        blob = (ROOT / f'data/pages/{page_id}.json').read_bytes()
        page = json.loads(blob)
        raw, reviewed = page['raw'], page.get('reviewed_text')
        if reviewed is None:
            continue
        reviewed_pages.append(page_id)
        edits = page['corrections']
        if page_id == 'lp1-10':
            assert len(edits) == 1 and 'start' not in edits[0]
            rune_positions = [i for i, symbol in enumerate(raw) if symbol in alphabet]
            start, end = rune_positions[116], rune_positions[117] + 1
            assert end == start + 2 and raw[start:end] == reviewed[start:end][::-1]
            assert raw[:start] + reviewed[start:end] + raw[end:] == reviewed
            edits = [dict(start=start, end=end, old=raw[start:end], new=reviewed[start:end],
                          note=edits[0]['note'], rune_positions_zero_based=[116, 117])]
        else:
            assert all(set(['start', 'end', 'old', 'new', 'note']) <= set(edit) for edit in edits), page_id
            rebuilt = raw
            for edit in reversed(edits):
                start, end = edit['start'], edit['end']
                assert rebuilt[start:end] == edit['old'], (page_id, start)
                rebuilt = rebuilt[:start] + edit['new'] + rebuilt[end:]
            assert rebuilt == reviewed, page_id
        for number, edit in enumerate(edits, 1):
            start, end = edit['start'], edit['end']
            line, column = line_column(raw, start)
            old, new = edit['old'], edit['new']
            kind = 'rune-order' if page_id == 'lp1-10' else 'non-rune-notation'
            if kind == 'non-rune-notation':
                assert all(symbol not in alphabet for symbol in old + new)
            locations.append(dict(id=f'{page_id}-{number}', page=page_id, kind=kind,
                                  archived_offset_zero_based=start, archived_end_exclusive=end,
                                  archived_line_one_based=line, archived_column_one_based=column,
                                  old=old, new=new, note=edit['note'],
                                  rune_positions_zero_based=edit.get('rune_positions_zero_based'),
                                  before=raw[max(0, start - 14):start],
                                  after=raw[end:end + 14],
                                  page_record_sha256=digest(blob),
                                  original_image_sha256=page['image_sha256']))
    boundary_blob = (ROOT / 'exports/page-boundaries.json').read_bytes()
    boundaries = json.loads(boundary_blob)['boundaries']
    candidates = [dict(left=row['left'], right=row['right'],
                       left_edge=row['left_edge'], right_edge=row['right_edge'],
                       visual_review=row['visual_review'], word_join=row['word_join'])
                  for row in boundaries if row['rune_to_rune']]
    assert len(locations) == sum(len(json.loads((ROOT / f'data/pages/{p}.json').read_text(encoding='utf-8'))['corrections']) for p in reviewed_pages)
    assert all(row['visual_review'] == 'not-performed' and row['word_join'] == 'undetermined' for row in candidates)
    return dict(schema='liberpedia-transcription-decisions-v1',
                scope='Published reviewed-layer edits and rune-to-rune LP2-00–55 page-edge candidates only; not an exhaustive visual audit of the manuscript.',
                alphabet_source_sha256=digest(index_bytes),
                boundary_inventory_sha256=digest(boundary_blob),
                counts=dict(reviewed_pages=len(reviewed_pages), edits=len(locations),
                            rune_order_edits=sum(row['kind'] == 'rune-order' for row in locations),
                            non_rune_edits=sum(row['kind'] == 'non-rune-notation' for row in locations),
                            unreviewed_rune_edges=len(candidates)),
                locations=locations, page_edge_candidates=candidates)


def render(data):
    grouped = defaultdict(list)
    for row in data['locations']:
        grouped[row['page']].append(row)
    parts = ['<div class="article-directory">']
    for page_id, rows in grouped.items():
        label = page_id.upper()
        parts.append(f'<p><a href="#/wiki/transcription-decisions?section=review-{page_id}" data-anchor="review-{page_id}">{label}</a> · {len(rows)} {"edit" if len(rows) == 1 else "edits"}</p>')
    parts.append('</div>')
    for page_id, rows in grouped.items():
        label = page_id.upper()
        parts.append(f'<h3 id="review-{page_id}">{label}</h3><p><a href="#/reader/{page_id}">Open original-image reader</a> · <a href="images/{page_id}.jpg" download>Download original JPEG</a> · <a href="data/pages/{page_id}.json" download>Structured page record</a>.</p>')
        for row in rows:
            old = escape(row['old']) if row['old'] else '∅'
            new = escape(row['new']) if row['new'] else '∅'
            position = (f'Archived rune positions {row["rune_positions_zero_based"][0]}–{row["rune_positions_zero_based"][1]} (zero-based); '
                        if row['rune_positions_zero_based'] else '')
            context = escape(row['before']) + '⟦' + (escape(row['old']) or 'cursor') + '⟧' + escape(row['after'])
            parts.append(f'<section id="{row["id"]}"><h4>Change {row["id"].rsplit("-", 1)[-1]}: <code>{old}</code> → <code>{new}</code></h4>'
                         f'<p>{position}Archived character offset {row["archived_offset_zero_based"]} (zero-based), '
                         f'text line {row["archived_line_one_based"]}, column {row["archived_column_one_based"]} (one-based). '
                         'This is a position in the stored text, not a measured image rectangle.</p>'
                         f'<pre class="reading-text">{context}</pre>'
                         f'<p class="small muted">{escape(row["note"])}</p></section>')
    edges = data['page_edge_candidates']
    parts.append('<h2 id="joins">Possible joins across LP2 page breaks</h2><p>At 32 of the 55 adjacent boundaries from LP2-00 through LP2-55, a rune is the last retained character on one page and a rune is the first on the next in the archived text. That observation does <strong>not</strong> say a word crosses the boundary. The images have not been checked for this inventory, and punctuation or section structure may change the interpretation. The complete <a href="exports/page-boundaries.json" download>55-boundary inventory</a> also contains the other 23 edges.</p><p>For a word-edge experiment, inspect both original images, record the treatment of the join, and rerun the calculation under both interpretations if uncertain.</p>')
    parts.append(f'<details><summary>Show all {len(edges)} rune-to-rune page edges</summary><div class="table-wrap"><table><thead><tr><th>Boundary</th><th>Archived edge</th><th>Interpretation</th></tr></thead><tbody>')
    for row in edges:
        parts.append(f'<tr><td><a href="#/reader/{row["left"]}">{row["left"].upper()}</a> → <a href="#/reader/{row["right"]}">{row["right"].upper()}</a></td><td><code>{escape(row["left_edge"])} | {escape(row["right_edge"])}</code></td><td>Word join undetermined; image review not performed</td></tr>')
    parts.append('</tbody></table></div></details>')
    return '\n'.join(parts)


def build():
    data = report()
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    start, end = '<!-- decision-register:start -->', '<!-- decision-register:end -->'
    source = ARTICLE.read_text(encoding='utf-8')
    assert source.count(start) == source.count(end) == 1
    left, rest = source.split(start, 1)
    _, right = rest.split(end, 1)
    ARTICLE.write_text(left + start + '\n' + render(data) + '\n' + end + right,
                       encoding='utf-8', newline='\n')
    print(f'Built {data["counts"]["edits"]} reviewed-layer positions and {data["counts"]["unreviewed_rune_edges"]} page-edge candidates.')


if __name__ == '__main__':
    if sys.argv[1:] == ['--check']:
        actual = report()
        expected = json.loads(OUTPUT.read_text(encoding='utf-8'))
        assert actual == expected, 'Saved location register differs from the bundled page records or boundary inventory'
        print(f'PASS: {actual["counts"]["edits"]} saved edits and {actual["counts"]["unreviewed_rune_edges"]} boundary candidates match their sources.')
    elif not sys.argv[1:]:
        build()
    else:
        raise SystemExit('Usage: python scripts/build_transcription_decisions.py [--check]')
