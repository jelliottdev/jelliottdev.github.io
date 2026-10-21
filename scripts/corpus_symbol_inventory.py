"""Offline inventory of symbols in all historical corpus prefixes.

Reads pinned Git blobs only; never executes source-repository code. Includes
short files separately from eligible 2902-token prefixes. Checkpoints retain
per-blob measurements; use a fresh directory when changing this script.
"""
import argparse
from collections import Counter
import hashlib
from itertools import islice
import json
import os
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
REVISION='a39e87ece3e6cbb0f00f7ad5fff9183da5c66d87'

def measure(raw,alphabet):
    text=raw.decode('utf-8',errors='strict')
    tokens=[m.group() for m in islice(re.finditer('[^ ]+',text),2902)]
    counts=Counter(c for token in tokens for c in token)
    outside={c:n for c,n in sorted(counts.items()) if c not in alphabet}
    return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
        'selected_tokens':len(tokens),'eligible':len(tokens)==2902,
        'counted_units':sum(counts.values()),'symbols':dict(sorted(counts.items())),
        'outside_alphabet':outside,
        'tokens_with_outside_symbols':sum(any(c not in alphabet for c in t) for t in tokens)}

def run(repo,output):
    env={**os.environ,'GIT_NO_LAZY_FETCH':'1'}
    git=lambda *args:subprocess.check_output(['git','-C',str(repo),*args],env=env)
    tree=git('ls-tree','-r','-z',REVISION)
    inventory=json.loads((ROOT/'exports/runeberg-inventory.json').read_bytes())
    assert hashlib.sha256(tree).hexdigest()==inventory['tree_listing_sha256']
    alphabet=''.join(a['rune'] for a in json.loads((ROOT/'data/index.json').read_bytes())['alphabet'])
    entries=[]
    for item in tree.split(b'\0'):
        if not item:continue
        meta,path=item.split(b'\t',1)
        if path.startswith(b'files/'):entries.append((path.decode(),meta.split()[2].decode()))
    assert len(entries)==25906
    output.mkdir(parents=True,exist_ok=True)
    spec={'revision':REVISION,'tree_sha256':hashlib.sha256(tree).hexdigest(),
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'alphabet':alphabet,'prefix_tokens':2902,
        'rule':'Strict UTF-8; literal spaces only; discard empty tokens; retain all code points. Short files separately reported. No normalization or inferred conversion.'}
    p=output/'specification.json'
    if p.exists():assert json.loads(p.read_bytes())==spec
    else:p.write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    if (output/'report.json').exists():raise ValueError('Complete report exists; choose a new output directory')
    cache=output/'blobs';cache.mkdir(exist_ok=True)
    rows=[]
    for i,(name,oid) in enumerate(sorted(entries),1):
        p=cache/(oid+'.json')
        if p.exists():row=json.loads(p.read_bytes())
        else:
            raw=git('cat-file','blob',oid)
            assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==oid
            row={'object_id':oid,**measure(raw,set(alphabet))}
            tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(row,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n');tmp.replace(p)
        assert row['object_id']==oid
        rows.append({'file':name,**row})
        if i%1000==0:print(f'{i}/25906 paths measured',flush=True)
    summaries={}
    for eligible in [True,False]:
        selected=[r for r in rows if r['eligible']==eligible]
        for weighting in ['paths','distinct_blobs']:
            group=selected if weighting=='paths' else list({r['object_id']:r for r in selected}.values())
            outside=Counter();presence=Counter()
            for row in group:
                outside.update(row['outside_alphabet']);presence.update(row['outside_alphabet'].keys())
            summaries[f'{"eligible" if eligible else "short"}_{weighting}']={
                'entries':len(group),'with_outside_symbols':sum(bool(r['outside_alphabet']) for r in group),
                'outside_occurrences':dict(sorted(outside.items())),
                'outside_entry_presence':dict(sorted(presence.items()))}
    report={'specification':spec,'complete':True,'records':rows,'summary':summaries,
        'limits':'Prefix symbol inventory only; no converter reconstruction, full-text symbol census, language inference or cipher conclusion. Cached rows require independent source verification.'}
    (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(summaries,ensure_ascii=True,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('repository',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.repository,a.output)
