"""Independently verify corpus-prefix symbols and reconcile the earlier census.

Uses literal-space splitting and scalar dictionaries, not the producer's regex
or Counter aggregation. Reads source blobs through one offline Git batch reader.
No receipt is produced for an incomplete or inconsistent report.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
digest=lambda raw:hashlib.sha256(raw).hexdigest()

def scan(raw,alphabet):
    tokens=[]
    for token in raw.decode('utf-8',errors='strict').split(' '):
        if token:tokens.append(token)
        if len(tokens)==2902:break
    symbols={};affected=0;lengths={}
    for token in tokens:
        bad=False
        lengths[str(len(token))]=lengths.get(str(len(token)),0)+1
        for c in token:
            symbols[c]=symbols.get(c,0)+1
            if c not in alphabet:bad=True
        affected+=bad
    return {'selected_tokens':len(tokens),'eligible':len(tokens)==2902,
        'counted_units':sum(len(t) for t in tokens),'symbols':symbols,
        'outside_alphabet':{c:n for c,n in symbols.items() if c not in alphabet},
        'tokens_with_outside_symbols':affected},lengths

def verify(repository,path):
    raw_report=path.read_bytes();report=json.loads(raw_report)
    assert report['complete'] is True
    spec=report['specification']
    assert spec['revision']=='a39e87ece3e6cbb0f00f7ad5fff9183da5c66d87' and spec['prefix_tokens']==2902
    assert spec['script_sha256']==digest((ROOT/'scripts/corpus_symbol_inventory.py').read_bytes())
    alphabet=''.join(a['rune'] for a in json.loads((ROOT/'data/index.json').read_bytes())['alphabet'])
    assert spec['alphabet']==alphabet
    env={**os.environ,'GIT_NO_LAZY_FETCH':'1'}
    tree=subprocess.check_output(['git','-C',str(repository),'ls-tree','-r','-z',spec['revision']],env=env)
    inventory=json.loads((ROOT/'exports/runeberg-inventory.json').read_bytes())
    assert digest(tree)==spec['tree_sha256']==inventory['tree_listing_sha256']
    entries=[]
    for item in tree.split(b'\0'):
        if not item:continue
        meta,name=item.split(b'\t',1)
        if name.startswith(b'files/'):entries.append((name.decode(),meta.split()[2].decode()))
    entries.sort();rows=report['records'];assert len(entries)==len(rows)==25906
    census_path=ROOT/'experiments/records/corpus-prefix-census/report.json'
    census_raw=census_path.read_bytes();census=json.loads(census_raw)
    assert census['complete'] and census['specification']['revision']==spec['revision']
    prior={r['file']:r for r in census['records']};assert set(prior)=={name for name,oid in entries}
    seen={};totals={}
    for status in ['eligible','short']:
        for weight in ['paths','distinct_blobs']:
            totals[status+'_'+weight]={'entries':0,'with_outside_symbols':0,'outside_occurrences':{},'outside_entry_presence':{}}
    process=subprocess.Popen(['git','-C',str(repository),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,env=env)
    try:
        for i,((name,oid),row) in enumerate(zip(entries,rows),1):
            assert row['file']==name and row['object_id']==oid
            duplicate=oid in seen
            if duplicate:expected,lengths=seen[oid]
            else:
                process.stdin.write((oid+'\n').encode());process.stdin.flush()
                head=process.stdout.readline().split()
                assert len(head)==3 and head[0].decode()==oid and head[1]==b'blob'
                size=int(head[2]);raw=process.stdout.read(size)
                assert len(raw)==size and process.stdout.read(1)==b'\n'
                assert hashlib.sha1(b'blob '+str(size).encode()+b'\0'+raw).hexdigest()==oid
                expected,lengths=scan(raw,set(alphabet))
                expected.update(bytes=size,sha256=digest(raw),object_id=oid)
                seen[oid]=(expected,lengths)
            assert {k:v for k,v in row.items() if k!='file'}==expected,name
            old=prior[name]
            for k in ['object_id','sha256','bytes','eligible']:assert old[k]==row[k],(name,k)
            if row['eligible']:
                assert old['statistics']['histogram']==lengths
                assert old['statistics']['counted_units']==row['counted_units']
            status='eligible' if row['eligible'] else 'short'
            for weight in (['paths'] if duplicate else ['paths','distinct_blobs']):
                total=totals[status+'_'+weight];total['entries']+=1
                total['with_outside_symbols']+=bool(row['outside_alphabet'])
                for c,n in row['outside_alphabet'].items():
                    total['outside_occurrences'][c]=total['outside_occurrences'].get(c,0)+n
                    total['outside_entry_presence'][c]=total['outside_entry_presence'].get(c,0)+1
            if i%1000==0:print(f'{i}/25906 source rows independently checked',flush=True)
    finally:
        process.stdin.close();process.stdout.close();process.wait()
    assert process.returncode==0 and len(seen)==25844
    assert totals==report['summary']
    return {'report_sha256':digest(raw_report),'checker_sha256':digest(Path(__file__).read_bytes()),
        'census_report_sha256':digest(census_raw),'paths_checked':len(rows),'distinct_blobs_checked':len(seen),
        'method':'Independent literal-space tokenization, scalar symbol counts, Git object identity, duplicate checks, and earlier census byte/eligibility/length-histogram reconciliation.',
        'limits':'Selected prefixes only; converter and edition provenance remain unknown.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('repository',type=Path);p.add_argument('report',type=Path);p.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args()
    if a.receipt.exists():p.error('Use a new receipt path')
    result=verify(a.repository,a.report)
    with a.receipt.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))
