"""Export readable CSV tables only from a complete, independently checked audit."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import unicodedata

def coverage_figure(summary):
    """Use identical proportion scales; retain exact numerators/denominators."""
    groups=[('eligible_paths','Eligible prefixes · count every path'),
        ('eligible_distinct_blobs','Eligible prefixes · identical bytes counted once'),
        ('short_paths','Short files · count every path'),
        ('short_distinct_blobs','Short files · identical bytes counted once')]
    parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 480" role="img" aria-labelledby="title desc">',
        '<title id="title">Prefixes and the stored rune alphabet</title>',
        '<desc id="desc">Four populations, each on a zero to one hundred percent scale. The colored portion counts entries containing at least one symbol outside the stored alphabet. Exact counts accompany every bar.</desc>',
        '<rect width="380" height="480" fill="white"/>',
        '<style>text{font:13px Arial,sans-serif;fill:#25343a}.note{font-size:12px}</style>',
        '<text x="18" y="27">Prefixes and the stored rune alphabet</text>',
        '<text x="18" y="50" class="note">Colored: at least one outside-alphabet symbol</text>']
    for i,(key,label) in enumerate(groups):
        s=summary[key];n=s['entries'];affected=s['with_outside_symbols']
        assert 0<=affected<=n
        y=85+83*i
        parts += [f'<text x="18" y="{y}">{label}</text>']
        if n:
            percent=100*affected/n
            parts += [f'<rect x="18" y="{y+12}" width="344" height="17" fill="#e6eaec"/>',
                f'<rect x="18" y="{y+12}" width="{344*affected/n:.4f}" height="17" fill="#42687b"/>',
                f'<text x="18" y="{y+49}">{affected:,} / {n:,} entries ({percent:.2f}%)</text>']
        else:parts += [f'<text x="18" y="{y+38}">No entries in this population</text>']
    parts += ['<text x="18" y="425" class="note">Eligible: first 2,902 nonempty literal-space tokens.</text>',
        '<text x="18" y="445" class="note">Short files: all available tokens, including empty files.</text>',
        '<text x="18" y="465" class="note">A symbol difference does not identify a language.</text>','</svg>']
    return '\n'.join(parts)+'\n'

def csv_text(header,rows):
    stream=io.StringIO(newline='');writer=csv.writer(stream,lineterminator='\n')
    writer.writerow(header);writer.writerows(rows)
    return stream.getvalue()

def render(report,receipt):
    raw=report.read_bytes();data=json.loads(raw);audit=json.loads(receipt.read_bytes())
    if not data.get('complete') or hashlib.sha256(raw).hexdigest()!=audit['report_sha256']:
        raise ValueError('A complete report and matching independent receipt are required')
    if audit['paths_checked']!=25906 or audit['distinct_blobs_checked']!=25844:
        raise ValueError('The independent receipt does not cover the complete pinned corpus')
    rows=[]
    for population,summary in sorted(data['summary'].items()):
        for char,count in sorted(summary['outside_occurrences'].items()):
            rows.append([population,f'U+{ord(char):04X}',unicodedata.name(char,'UNNAMED'),
                summary['entries'],summary['outside_entry_presence'][char],count])
    files=[]
    for row in data['records']:
        files.append([row['file'],row['object_id'],row['sha256'],
            'eligible' if row['eligible'] else 'short',row['selected_tokens'],row['counted_units'],
            row['tokens_with_outside_symbols'],sum(row['outside_alphabet'].values()),
            '; '.join(f'U+{ord(c):04X}={n}' for c,n in sorted(row['outside_alphabet'].items()))])
    populations=[[name,s['entries'],s['with_outside_symbols'],s['entries']-s['with_outside_symbols']]
        for name,s in sorted(data['summary'].items())]
    return {
        'coverage.svg':coverage_figure(data['summary']),
        'symbols.csv':csv_text(['population','code_point','unicode_name','population_entries','entries_containing_symbol','symbol_occurrences'],rows),
        'files.csv':csv_text(['path','git_blob_id','sha256','prefix_status','selected_tokens','counted_units','tokens_with_outside_symbols','outside_symbol_occurrences','outside_symbol_counts'],files),
        'populations.csv':csv_text(['population','entries','entries_with_outside_symbols','entries_using_only_stored_alphabet'],populations),
        'README.txt':('Historical corpus prefix symbol inventory\n\n'
            'Report SHA-256: '+audit['report_sha256']+'\n'
            'Revision: '+data['specification']['revision']+'\n'
            'Unicode name database: '+unicodedata.unidata_version+'\n\n'
            'Eligible means at least 2,902 literal-space tokens; only that prefix is inspected.\n'
            'Short files contribute their available tokens to separate populations.\n'
            'Path weighting counts every source path. Distinct-blob weighting counts identical bytes once.\n'
            'Entries containing a symbol and occurrences of that symbol are different counts.\n'
            'Symbols absent from all entries have no row in symbols.csv; populations.csv retains zero cases.\n'
            'The alphabet comparison supplies no intended converter, source-language identification, or cipher rule.\n')}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('report',type=Path);p.add_argument('receipt',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();outputs=render(a.report,a.receipt)
    a.output.mkdir(parents=True,exist_ok=False)
    for name,content in outputs.items():(a.output/name).write_text(content,encoding='utf-8',newline='\n')
    print('Exported verified per-file, per-symbol and population tables')
