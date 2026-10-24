"""Bounded H-02 raw-byte census. No cipher search and no network access."""
import argparse
import collections
import hashlib
import json
import re
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
G02 = ROOT / 'experiments/records/dukotah-g02-signature-corpus'
BEGIN = b'-----BEGIN PGP SIGNED MESSAGE-----'
SIG = b'-----BEGIN PGP SIGNATURE-----'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def write(name, value):
    (HERE/name).write_text(json.dumps(value, indent=2, sort_keys=True)+'\n', encoding='utf-8', newline='\n')

def lines(raw):
    # Preserve content bytes, terminators and leading indentation separately.
    return [(m.group(1), m.group(2)) for m in re.finditer(rb'([^\r\n]*)(\r\n|\n|\r|$)', raw) if m.group(0)]

def extract(raw):
    ls = lines(raw)
    bodies, rejected = [], []
    for i, (line, _) in enumerate(ls):
        if line != BEGIN:
            continue
        j = i+1
        headers = []
        while j < len(ls) and ls[j][0] != b'':
            headers.append(ls[j][0]); j += 1
        if not headers or any(not x.startswith(b'Hash: ') for x in headers) or j == len(ls):
            rejected.append({'line': i+1, 'reason': 'invalid or absent Hash header / separator'}); continue
        start = j+1
        end = next((k for k in range(start, len(ls)) if ls[k][0] == SIG), None)
        if end is None:
            rejected.append({'line': i+1, 'reason': 'missing signature boundary'}); continue
        if not any(x[0] == b'-----END PGP SIGNATURE-----' for x in ls[end+1:]):
            rejected.append({'line': i+1, 'reason': 'missing signature end'}); continue
        bodies.append((i+1, start+1, ls[start:end]))
    return bodies, rejected

def analyze(body):
    rows=[]
    for i, (content, ending) in enumerate(body, 1):
        suffix = content[len(content.rstrip(b' \t')):]
        rows.append({'line': i, 'spaces': suffix.count(b' '), 'tabs': suffix.count(b'\t'),
                     'pattern': suffix.decode('ascii').replace(' ', 's').replace('\t', 't'),
                     'content_sha256': sha(content), 'line_ending': {b'\n':'LF',b'\r\n':'CRLF',b'\r':'CR',b'':'none'}[ending]})
    exact = b''.join(c+e for c,e in body)
    # Canonical here means dash-unescaped, trailing space/tab stripped, LF-joined.
    canonical = b'\n'.join((c[2:] if c.startswith(b'- ') else c).rstrip(b' \t') for c,e in body)
    nz=[r['spaces']+r['tabs'] for r in rows if r['pattern']]
    known=json.loads((HERE/'plan.json').read_text())['fixed_sequences']
    matches=[name+(' (exact)' if nz == seq else ' (prefix)') for name,seq in known.items() if nz[:len(seq)] == seq]
    return {'exact_body_sha256':sha(exact),'canonical_body_sha256':sha(canonical),
            'line_count':len(rows),'whitespace_lines':sum(bool(r['pattern']) for r in rows),
            'trailing_spaces':sum(r['spaces'] for r in rows),'trailing_tabs':sum(r['tabs'] for r in rows),
            'nonzero_counts':nz,'fixed_sequence_matches':matches,'lines':rows}

def fixture_check():
    out=[]
    for fixture in json.loads((HERE/'fixtures.json').read_text()):
        body, rejected=extract(fixture['raw'].encode('ascii'))
        got=[analyze(x[2]) for x in body]
        observed=[[r['pattern'] for r in b['lines']] for b in got]
        assert observed == fixture['patterns'], (fixture['name'],observed)
        assert len(rejected) == fixture['rejected'], fixture['name']
        out.append({'name':fixture['name'],'pass':True})
    return out

def compute():
    plan=json.loads((HERE/'plan.json').read_text())
    for item in plan['inputs']:
        assert sha((ROOT/item['path']).read_bytes()) == item['sha256'], item['path']
    controls=fixture_check()
    aliases=json.loads((G02/'sources/path-aliases.json').read_text())['paths']
    verdicts={r['path']:r['gpg_verdict'] for r in json.loads((G02/'independent-verification.json').read_text())['rows']}
    rows=[]
    rejected=[]
    excluded=collections.Counter()
    with zipfile.ZipFile(G02/'sources/asc-blobs.zip') as z:
        for entry in aliases:
            raw=z.read('blobs/'+entry['sha256'])
            assert sha(raw) == entry['sha256'] and len(raw) == entry['bytes']
            bodies, bad=extract(raw)
            rejected.extend(dict(path=entry['path'],**x) for x in bad)
            if not bodies:
                excluded[verdicts[entry['path']]] += 1
            for bi,(opening,start,body) in enumerate(bodies):
                rows.append(dict(path=entry['path'],block=bi,raw_sha256=entry['sha256'],
                                 body_start_line=start,g02_verdict=verdicts[entry['path']],**analyze(body)))
    exact=collections.defaultdict(list); canonical=collections.defaultdict(list)
    for row in rows:
        exact[row['exact_body_sha256']].append(row)
        canonical[row['canonical_body_sha256']].append(row)
    exact_reps=[rs[0] for rs in exact.values()]
    differences=[]
    for digest,rs in canonical.items():
        variants=sorted(set(r['exact_body_sha256'] for r in rs))
        if len(variants)>1:
            differences.append({'canonical_body_sha256':digest,'exact_variants':variants,
                                'copies':[{'path':r['path'],'body_sha256':r['exact_body_sha256'],
                                          'nonzero_counts':r['nonzero_counts']} for r in rs]})
    return {'schema':'liberpedia-h02-raw-whitespace-v1','plan_sha256':sha((HERE/'plan.json').read_bytes()),
            'source_paths':len(aliases),'source_unique_files':len(set(x['sha256'] for x in aliases)),
            'parsed_blocks':len(rows),'parsed_paths':len(set(r['path'] for r in rows)),
            'excluded_paths_by_g02_verdict':dict(excluded),'rejected_blocks':rejected,
            'exact_unique_bodies':len(exact),'canonical_unique_bodies':len(canonical),
            'path_weighted_whitespace_bodies':sum(r['whitespace_lines']>0 for r in rows),
            'exact_unique_whitespace_bodies':sum(r['whitespace_lines']>0 for r in exact_reps),
            'exact_unique_body_lines':sum(r['line_count'] for r in exact_reps),
            'exact_unique_whitespace_lines':sum(r['whitespace_lines'] for r in exact_reps),
            'exact_unique_trailing_spaces':sum(r['trailing_spaces'] for r in exact_reps),
            'exact_unique_trailing_tabs':sum(r['trailing_tabs'] for r in exact_reps),
            'fixed_match_exact_bodies':sum(bool(r['fixed_sequence_matches']) for r in exact_reps),
            'canonical_groups_with_multiple_exact_variants':differences,'controls':controls,'rows':rows}

if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--check',action='store_true'); args=parser.parse_args()
    result=compute()
    if args.check:
        assert result == json.loads((HERE/'results.json').read_text())
    else:
        write('results.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','canonical_groups_with_multiple_exact_variants')},indent=2))
