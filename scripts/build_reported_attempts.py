"""Render source-specific, not-yet-replayed work outside the experiment registry."""
from collections import Counter
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/reported-attempts.json'
OUTPUT = ROOT / 'articles/reported-attempts.html'
LABELS = {'not-replayed': 'Not replayed', 'related-only': 'Related work only',
          'partial': 'Partly replayed'}

def e(value):
    return escape(str(value), quote=True)

def build():
    register = json.loads(DATA.read_text(encoding='utf-8'))
    entries = register['entries']
    reconciled = register.get('reconciled_sources', [])
    assert register['schema'] == 'liberpedia-reported-attempts-v1'
    assert len(entries) == len({item['id'] for item in entries})
    published = {record['id'] for record in json.loads((ROOT / 'data/experiments.json').read_text(encoding='utf-8'))['records']}
    families = {family['id']: family for family in json.loads((ROOT / 'data/method-families.json').read_text(encoding='utf-8'))['families']}
    parts = [f'<p>This intake currently names <strong>{len(entries)} source-specific proposals or analyses</strong>. '
             'They are reports of prior work, not completed Liberpedia experiments. Each entry separates the original idea, '
             'our narrower coverage, and the missing steps for an exact replay. A related record never closes the reported idea by itself.</p>',
             '<p>The supplied text files are identified by SHA-256 and attribution; their full contents are not republished here. '
             'A public link, when present, may change and has not yet been pinned to a revision. '
             'Start with <a href="#/experiments">Have we tried it?</a> for completed records, '
             'or the <a href="#/wiki/solving-methods">method map</a> for a broader family.</p>']
    counts = Counter(item['status'] for item in entries)
    parts.append('<p class="small muted">' + ' · '.join(f'{e(LABELS[s])}: {counts[s]}' for s in LABELS if counts[s]) + '</p>')
    parts.append('<nav aria-label="Reported attempt index"><h2 id="index">Find an attempt</h2><ul>')
    for item in entries:
        parts.append(f'<li><a href="#/wiki/reported-attempts?section={e(item["id"])}">{e(item["title"])}</a> '
                     f'<span class="small muted">· {e(LABELS[item["status"]])}</span></li>')
    parts.append('</ul></nav><h2 id="entries">Source-specific entries</h2>')
    for item in entries:
        assert item['status'] in LABELS and item['family'] in families
        assert all(record in published for record in item['related_records'])
        source = item['source']
        assert len(source['sha256']) == 64 and all(char in '0123456789abcdef' for char in source['sha256'])
        family = families[item['family']]
        parts.append(f'<section id="{e(item["id"])}"><h3>{e(item["title"])}</h3>'
                     f'<p class="small muted">{e(LABELS[item["status"]])} · '
                     f'<a href="#/wiki/{e(family["guide"])}">{e(family["title"])}</a>'
                     + (f' · {", ".join(e(p.upper()) for p in item["pages"])}' if item['pages'] else '') + '</p>'
                     f'<p><strong>Reported approach.</strong> {e(item["reported_idea"])}</p>'
                     f'<p><strong>Current archive coverage.</strong> {e(item["coverage"])}</p>'
                     f'<p><strong>Replay requirement.</strong> {e(item["replay_needed"])}</p>')
        if item['related_records']:
            links = ', '.join(f'<a href="#/experiments/{e(record)}">{e(record.replace("-", " "))}</a>'
                              for record in item['related_records'])
            parts.append(f'<p><strong>Related records with narrower scopes:</strong> {links}.</p>')
        parts.append(f'<details><summary>Source identification</summary><p>{e(source["title"])} · '
                     f'{e(source["author"])} · {e(source["reported"])}. '
                     f'Supplied transcript SHA-256: <code>{e(source["sha256"])}</code>.</p>')
        if source.get('public_url'):
            parts.append(f'<p><a href="{e(source["public_url"])}">Related public material</a> '
                         '(current URL; exact version not yet pinned).</p>')
        parts.append('</details></section>')
    if reconciled:
        parts.append('<h2 id="reconciled">Source notes with a reproduced scope</h2>'
                     '<p>These supplied notes point to work already checked here. The link covers only the precise claim described, not every suggestion in its source thread.</p><ul>')
        for item in reconciled:
            assert ('experiment' in item) != ('guide' in item)
            if 'experiment' in item:
                assert item['experiment'] in published
                link = f'#/experiments/{e(item["experiment"])}'
            else:
                link = f'#/wiki/{e(item["guide"])}'
            parts.append(f'<li><strong>{e(item["title"])}</strong> · {e(item["author"])}. '
                         f'{e(item["covered_scope"])} <a href="{link}">Read the checked scope</a>. '
                         f'<span class="small muted">Source SHA-256: <code>{e(item["sha256"])}</code></span></li>')
        parts.append('</ul>')
    parts.append('<p>The register is an intake, not a census of all historical solver work. '
                 'Its entries should be promoted to completed experiments only after their inputs, exact rule, '
                 'controls and outputs have been saved and independently checked. '
                 '<a href="data/reported-attempts.json" download>Download the structured intake</a>.</p>')
    OUTPUT.write_text('\n'.join(parts) + '\n', encoding='utf-8', newline='\n')
    print(f'Built {len(entries)} source-specific reported-attempt entries.')

if __name__ == '__main__':
    build()
