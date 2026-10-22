"""Build a compact method directory from its declared guide and record links."""
import html
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: json.loads((ROOT / path).read_text(encoding='utf-8'))
family_data = read('data/method-families.json')
families = family_data['families']
record_kinds = family_data['record_kinds']
record_kind_by_id = family_data['record_kind_by_id']
experiments = {row['id']: row for row in read('data/experiments.json')['records']}
guides = {row['id'] for row in read('articles/index.json')}
assert set(record_kind_by_id) == set(experiments)
assert all(kind in record_kinds for kind in record_kind_by_id.values())
assert len({family['id'] for family in families}) == len(families)

e = html.escape
groups = list(dict.fromkeys(family['group'] for family in families))
counts = Counter(family['group'] for family in families)
anchor = lambda group: group.lower().replace(',', '').replace(' ', '-')
parts = [
    '<p>Choose the kind of approach you want to try. Each family links to an explanation and, where available, records of specific tests. A listed test covers its stated variant, not every possible version of the idea.</p>',
    '<p>For example, “read the runes in a spiral” still needs a page, starting point, direction and rule for reading the result. <a href="#/experiments">Have we tried it?</a> compares those exact choices.</p>',
    '<nav class="method-jump" aria-label="Method categories"><strong>Jump to a category</strong><ul>'
    + ''.join(f'<li><a href="#/wiki/solving-methods?section={anchor(group)}">{e(group)}</a> <span>{counts[group]}</span></li>' for group in groups)
    + '</ul></nav>',
]

linked = set()
for group in groups:
    parts.append(f'<section class="method-group"><h2 id="{anchor(group)}">{e(group)}</h2>'
                 f'<details><summary>{counts[group]} method {"family" if counts[group] == 1 else "families"}</summary>'
                 '<div class="method-family-list">')
    for family in (row for row in families if row['group'] == group):
        assert family['guide'] in guides
        assert len(family['related']) == len(set(family['related'])), family['id']
        records = [experiments[record_id] for record_id in family['related']]
        assert all(record['status'] == 'published' for record in records)
        linked.update(record['id'] for record in records)
        parts.append(f'<section class="method-family" id="family-{e(family["id"])}">'
                     f'<h3><a href="#/wiki/{e(family["guide"])}">{e(family["title"])}</a></h3>'
                     f'<p>{e(family["description"])}</p>')
        if records:
            parts.append(f'<details><summary>{len(records)} related {"record" if len(records) == 1 else "records"}</summary><ul>')
            for record in records:
                kind = record_kinds[record_kind_by_id[record['id']]]['label']
                parts.append(f'<li><a href="#/experiments/{e(record["id"])}">{e(record["title"])}</a>'
                             f' <span class="small muted">· {e(kind)}</span></li>')
            parts.append('</ul></details>')
        parts.append('</section>')
    parts.append('</div></details></section>')

parts.append('<h2 id="record-types">Reading the records</h2>'
             '<p>Tests, measurements and source checks answer different questions. Open a record for its result and exact limits.</p>'
             '<details><summary>What each record type means</summary><dl>'
             + ''.join(f'<dt>{e(kind["label"])}</dt><dd>{e(kind["description"])}</dd>' for kind in record_kinds.values())
             + '</dl></details>')
parts.append('<h2 id="narrowing">Turn a method into a test</h2>'
             '<p>Fix the input, rule and stopping point before checking whether an output looks promising. '
             'For a spiral, that means naming the page, grid, start, direction and what counts as a result. '
             '<a href="#/wiki/search-space">Learn why bounds matter</a> · '
             '<a href="data/method-families.json" download>Download the complete method map</a>.</p>')
(ROOT / 'articles/solving-methods.html').write_text('\n'.join(parts) + '\n', encoding='utf-8', newline='\n')
print(f'Built {len(families)} families linking {len(linked)} distinct experiment records; associations are not exhaustive coverage claims.')
