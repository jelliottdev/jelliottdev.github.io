"""Build the method-family directory from its declared guide and experiment links."""
import html
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
read=lambda p:json.loads((ROOT/p).read_text(encoding='utf-8'))
family_data=read('data/method-families.json')
families=family_data['families']
record_kinds=family_data['record_kinds']
record_kind_by_id=family_data['record_kind_by_id']
experiments={r['id']:r for r in read('data/experiments.json')['records']}
assert set(record_kind_by_id)==set(experiments)
assert all(kind in record_kinds for kind in record_kind_by_id.values())
guides={r['id'] for r in read('articles/index.json')}
assert len({f['id'] for f in families})==len(families)
parts=['''<p>Start with the kind of operation an idea proposes, then narrow it to a specific rule and test. This map includes decoding methods, ways to search for keys, and diagnostic checks. They overlap: a proposal can combine a route, a numerical key and a reset rule. Combining families adds choices that must be counted.</p>
<p><strong>A family page is not a completed experiment.</strong> Open its guide to understand the method, or expand its linked records to compare the exact questions tested. The records cover only their stated inputs, variants and bounds. No linked record means a gap in this map, not an untouched or promising approach.</p>''']
parts.append('<p><a href="#/wiki/solving-methods?section=record-types">What the record types mean</a>: distinguish bounded solving tests from measurements, controls, audits and reproductions.</p>')
linked=set()
for group in dict.fromkeys(f['group'] for f in families):
    anchor=group.lower().replace(',','').replace(' ','-')
    parts.append(f'<h2 id="{anchor}">{html.escape(group)}</h2><dl>')
    for family in (f for f in families if f['group']==group):
        assert family['guide'] in guides
        parts.append(f'<dt id="family-{family["id"]}"><a href="#/wiki/{family["guide"]}">{html.escape(family["title"])}</a></dt><dd><p>{html.escape(family["description"])}</p>')
        records=[experiments[eid] for eid in family['related']]
        assert all(r['status']=='published' for r in records)
        if records:
            linked.update(r['id'] for r in records)
            parts.append(f'<details><summary>Related records ({len(records)})</summary><p>Compare these questions and exclusions with your proposal. A linked result does not cover every variant of this family.</p><ul>')
            for r in records:
                kind=record_kinds[record_kind_by_id[r['id']]]
                parts.append(f'<li><p><a href="#/experiments/{r["id"]}">{html.escape(r["title"])}</a></p><p><strong>Record type:</strong> {html.escape(kind["label"])}. {html.escape(kind["description"])}</p><p><strong>Question tested:</strong> {html.escape(r["question"])}</p><p><strong>Outside this test:</strong> {html.escape(r["scope"]["exclusions"])}</p></li>')
            parts.append('</ul></details>')
        else:
            parts.append('<p class="small muted">No experiment linked yet. The guide documents the approach; it is not a result.</p>')
        parts.append('</dd>')
    parts.append('</dl>')
parts.append('<h2 id="record-types">What the record types mean</h2><dl>'+''.join(f'<dt>{html.escape(kind["label"])}</dt><dd>{html.escape(kind["description"])}</dd>' for kind in record_kinds.values())+'</dl><p>These describe the role of a record, not its outcome or confidence. A control linked to a method is not a test of that method on every unsolved page.</p>')
parts.append('''<h2 id="narrowing">From a family to a test</h2><p>For example, “try spirals” names a route family. A test must also fix the pages, grid dimensions, padding, starting cell, directions, any added substitution and the criterion for success. Changing one of these choices creates a variant; changing several may create a new experiment family.</p><p>Use <a href="#/experiments">Have we tried it?</a> to inspect published scope. Related methods can be useful even when the exact variant is not covered. <a href="data/method-families.json" download>Download the family map</a>.</p>''')
(ROOT/'articles/solving-methods.html').write_text('\n'.join(parts)+'\n',encoding='utf-8',newline='\n')
print(f'Built {len(families)} families linking {len(linked)} distinct experiment records; associations are not exhaustive coverage claims.')
