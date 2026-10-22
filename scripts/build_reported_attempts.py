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
    queue = register.get('screening_queue', [])
    screening = json.loads((ROOT / 'data/source-screening.json').read_text(encoding='utf-8'))
    assert screening['schema'] == 'liberpedia-source-screening-v1'
    screening_by_id = {item['attachment_id']: item for item in screening['sources']}
    assert len(screening_by_id) == len(screening['sources'])
    assert set(screening_by_id) <= {item['attachment_id'] for item in queue}
    assert all(item['disposition'] in ('closed', 'followup') for item in screening['sources'])
    assert all((ROOT / item['audit_note']).is_file() for item in screening['sources'])
    screened = len(screening_by_id)
    open_followups = sum(item['disposition'] == 'followup' for item in screening['sources'])
    unscreened = len(queue) - screened
    assert register['schema'] == 'liberpedia-reported-attempts-v1'
    assert len(entries) == len({item['id'] for item in entries})
    published = {record['id'] for record in json.loads((ROOT / 'data/experiments.json').read_text(encoding='utf-8'))['records']}
    families = {family['id']: family for family in json.loads((ROOT / 'data/method-families.json').read_text(encoding='utf-8'))['families']}
    unique_sources = {item['source']['attachment_id'] for item in entries} | {item['attachment_id'] for item in reconciled} | {item['attachment_id'] for item in queue}
    entry_sources = {item['source']['attachment_id'] for item in entries}
    linked_entries = sum(bool(item['source'].get('public_url')) for item in entries)
    reconciled_sources = {item['attachment_id'] for item in reconciled}
    queued_sources = {item['attachment_id'] for item in queue}
    memberships = len(entry_sources) + len(reconciled_sources) + len(queued_sources)
    overlapping_files = sum(sum(source in group for group in
                                (entry_sources, reconciled_sources, queued_sources)) > 1
                            for source in unique_sources)
    counts = Counter(item['status'] for item in entries)
    assert sum(counts.values()) == len(entries)
    parts = [f'<p>This intake draws on <strong>{len(unique_sources)} distinct supplied source files</strong>. '
             f'It contains <strong>{len(entries)} source-specific proposal or analysis entries from {len(entry_sources)} files</strong>, '
             f'<strong>{len(reconciled)} checked-scope notes from {len(reconciled_sources)} files</strong>, and '
             f'<strong>{screened} screened source files</strong> ({open_followups} with specific follow-ups, '
             f'{screened - open_followups} with no further distinct claim in the supplied file), and '
             f'<strong>{unscreened} files not yet screened</strong>. '
             f'These are different units: {len(entries)} counts entries, while {len(unique_sources)} counts distinct files. '
             f'The three file lists have {memberships} memberships because {overlapping_files} files appear in more than one list; '
             f'their overlap accounts for {memberships - len(unique_sources)} repeated memberships. '
             'A source can yield several entries, have a checked observation, and retain a narrower follow-up after screening. '
             'They are reports of prior work, not completed Liberpedia experiments. Each entry separates the original idea, '
             'our narrower coverage, and the missing steps for an exact replay. A related record never closes the reported idea by itself.</p>',
             '<p>The supplied text files are identified by SHA-256 and attribution; their full contents are not republished here. '
             f'Of the {len(entries)} source-specific entries, <strong>{linked_entries} link to related public material</strong> and '
             f'<strong>{len(entries) - linked_entries} have no public URL recorded</strong>. Even a related public link may not expose the exact supplied post. A hash verifies a copy someone already holds; '
             'it cannot retrieve a private transcript or independently establish the attribution. '
             'These entries are source leads, not a complete public history of prior attempts. '
             'A public link, when present, may change and has not yet been pinned to a revision. '
             'Start with <a href="#/experiments">Have we tried it?</a> for completed records, '
             'or the <a href="#/wiki/solving-methods">method map</a> for a broader family.</p>']
    parts.append('<p class="small muted">Entry status (one per proposal): ' + ' · '.join(f'{e(LABELS[s])}: {counts[s]}' for s in LABELS if counts[s]) + f' · Total: {len(entries)}</p>')
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
        if item.get('related_guides'):
            links = ', '.join(f'<a href="#/wiki/{e(guide)}">{e(guide.replace("-", " "))}</a>'
                              for guide in item['related_guides'])
            parts.append(f'<p><strong>Related source guide:</strong> {links}.</p>')
        parts.append(f'<details><summary>Source identification</summary><p>{e(source["title"])} · '
                     f'{e(source["author"])} · {e(source["reported"])}. '
                     f'Supplied transcript SHA-256: <code>{e(source["sha256"])}</code>.</p>')
        if source.get('public_url'):
            parts.append(f'<p><a href="{e(source["public_url"])}">Related public material</a> '
                         + (f'(repository revision <code>{e(source["public_revision"])}</code>; correspondence to the historical input may still be unresolved).'
                            if source.get('public_revision') else '(current URL; exact version not yet pinned).')
                         + '</p>')
        else:
            parts.append('<p>No public URL is recorded for this source. The supplied transcript hash is not a retrievable citation.</p>')
        parts.append('</details></section>')
    if reconciled:
        parts.append('<h2 id="reconciled">Source notes with a reproduced scope</h2>'
                     '<p>These supplied notes point to work already checked here. The link covers only the precise claim described, not every suggestion in its source thread. A file may also appear in the screening queue when it contains other claims.</p><ul>')
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
    if queue:
        parts.append('<h2 id="screening-queue">Screened source files and follow-ups</h2>'
                     '<p>The supplied files below have a claim-by-claim intake note where indicated. '
                     'Screened means the pasted extract was classified; it does not mean its reported methods were replayed, '
                     'its missing attachments recovered, or all public solver work covered.</p>')
        for disposition, heading in [('followup', 'Specific follow-ups'), ('closed', 'No further distinct claim in the supplied file')]:
            subset = [item for item in queue if item['attachment_id'] in screening_by_id
                      and screening_by_id[item['attachment_id']]['disposition'] == disposition]
            if not subset:
                continue
            parts.append(f'<h3>{e(heading)} <span class="small muted">({len(subset)})</span></h3><ul>')
            for item in subset:
                audit = screening_by_id[item['attachment_id']]
                parts.append(f'<li><strong>{e(item["label"])}</strong> · {e(audit["summary"])} '
                             f'<a href="{e(audit["audit_note"])}">Read the source-intake note</a>. '
                             f'<details><summary>Source ID and checksum</summary><p class="small muted">'
                             f'{e(item["attachment_id"])} · SHA-256: <code>{e(item["sha256"])}</code>'
                             '</p></details></li>')
            parts.append('</ul>')
        lanes = [
            ('compare-existing', 'Compare with existing coverage'),
            ('extract-new', 'Extract a testable method or source claim'),
            ('context-check', 'Check whether the note contains an experiment'),
            ('exclusion-check', 'Check whether the file belongs in this archive'),
        ]
        for lane, heading in lanes:
            subset = [item for item in queue if item['attachment_id'] not in screening_by_id and item['triage_lane'] == lane]
            if not subset:
                continue
            parts.append(f'<h3>{e(heading)} <span class="small muted">({len(subset)})</span></h3><ul>')
            for item in subset:
                parts.append(f'<li><strong>{e(item["label"])}</strong> · {e(item["next_check"])} '
                             f'<details><summary>Source ID and checksum</summary><p class="small muted">'
                             f'{e(item["attachment_id"])} · SHA-256: <code>{e(item["sha256"])}</code>'
                             '</p></details></li>')
            parts.append('</ul>')
    parts.append('<p>The register is an intake, not a census of all historical solver work. '
                 'Its entries should be promoted to completed experiments only after their inputs, exact rule, '
                 'controls and outputs have been saved and independently checked. '
                 '<a href="data/reported-attempts.json" download>Download the structured intake</a>.</p>')
    OUTPUT.write_text('\n'.join(parts) + '\n', encoding='utf-8', newline='\n')
    print(f'Built {len(entries)} source-specific reported-attempt entries.')

if __name__ == '__main__':
    build()
