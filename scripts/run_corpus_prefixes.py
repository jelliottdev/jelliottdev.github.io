"""Resumable full pinned-corpus prefix measurement. No external source code runs.

Default is offline: missing Git objects stop the run without a complete report.
--allow-fetch permits the partial clone to retrieve missing blobs. This may
download gigabytes. Checkpoints reuse identical blobs but final rows preserve
each file's weight. Never call a partial run a corpus comparison.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from corpus_prefix_statistics import prefix, summarize

ROOT=Path(__file__).resolve().parents[1]
REVISION='a39e87ece3e6cbb0f00f7ad5fff9183da5c66d87'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def run(repository, output, allow_fetch=False):
    env=os.environ.copy()
    if not allow_fetch:
        env['GIT_NO_LAZY_FETCH']='1'
    def git(*args):
        return subprocess.check_output(['git','-C',str(repository),*args],env=env)
    tree=git('ls-tree','-r','-z',REVISION)
    expected=json.loads((ROOT/'exports/runeberg-inventory.json').read_bytes())
    assert hashlib.sha256(tree).hexdigest()==expected['tree_listing_sha256']
    entries=[]
    for item in tree.split(b'\0'):
        if item:
            meta,path=item.split(b'\t',1)
            if path.startswith(b'files/'):
                entries.append((path.decode(),meta.split()[2].decode()))
    assert len(entries)==25906
    entries.sort()
    spec={'revision':REVISION,'tree_sha256':expected['tree_listing_sha256'],'prefix_tokens':2902,
          'calculator_sha256':sha(ROOT/'scripts/corpus_prefix_statistics.py'),
          'runner_sha256':sha(Path(__file__)),
          'conventions':'UTF-8 strict; literal spaces; discard empty slots; count all remaining Unicode code points. No deduplication, header removal, symbol filtering or language selection. Sample variance n-1; linear quantiles at (n-1)q.'}
    output.mkdir(parents=True,exist_ok=True)
    if (output/'report.json').exists():
        raise SystemExit('Complete report already exists; retain it and use a new output directory for a rerun')
    specification=output/'specification.json'
    if specification.exists():
        assert json.loads(specification.read_bytes())==spec,'Changed run specification: use another output directory'
    else:
        specification.write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8')
    cache=output/'blobs';cache.mkdir(exist_ok=True)
    records=[]
    for number,(name,oid) in enumerate(entries,1):
        path=cache/(oid+'.json')
        if path.exists():
            row=json.loads(path.read_bytes())
            assert row['object_id']==oid
        else:
            try:
                raw=git('cat-file','blob',oid)
            except subprocess.CalledProcessError:
                raise SystemExit(f'Stopped before {name}: Git object unavailable. {len(records)} entries processed; no complete report written. Retain this directory to resume with the same specification.') from None
            assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==oid
            lengths=prefix(raw)
            row={'object_id':oid,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),
                 'eligible':lengths is not None,'statistics':summarize(lengths) if lengths is not None else None}
            temporary=path.with_suffix('.tmp')
            temporary.write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8')
            temporary.replace(path)
        records.append({'file':name,**row})
        if number%250==0: print(f'{number}/25906 file entries processed',flush=True)
    report={'specification':spec,'complete':True,'entries':len(records),
            'eligible_entries':sum(r['eligible'] for r in records),'records':records,
            'limits':'Descriptive corpus-prefix census; no tail calculation or manuscript-language inference. Cached measurement files must be retained and independently audited before publication.'}
    temporary=output/'report.tmp'
    temporary.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    temporary.replace(output/'report.json')
    print(f"Complete: {report['entries']} entries; {report['eligible_entries']} eligible")


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('repository',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--allow-fetch',action='store_true')
    a=p.parse_args()
    run(a.repository,a.output,a.allow_fetch)
