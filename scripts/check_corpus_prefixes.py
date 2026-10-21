"""Independently audit a complete census against pinned Git blobs, offline.

Uses regex tokenization, statistics module aggregations, and one Git batch
reader rather than the producer's parsing/calculation functions or checkpoints.
No corpus source code runs. An optional audit receipt is created only on success.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import re
import statistics
import subprocess

ROOT=Path(__file__).resolve().parents[1]
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def check(repository, report_path):
    raw_report=report_path.read_bytes()
    report=json.loads(raw_report)
    spec=report['specification']
    assert report['complete'] is True and spec['prefix_tokens']==2902
    assert spec['revision']=='a39e87ece3e6cbb0f00f7ad5fff9183da5c66d87'
    env=os.environ.copy();env['GIT_NO_LAZY_FETCH']='1'
    tree=subprocess.check_output(['git','-C',str(repository),'ls-tree','-r','-z',spec['revision']],env=env)
    assert sha(tree)==spec['tree_sha256']
    entries=[]
    for item in tree.split(b'\0'):
        if item:
            meta,name=item.split(b'\t',1)
            if name.startswith(b'files/'):
                entries.append((name.decode(),meta.split()[2].decode()))
    entries.sort()
    rows=report['records']
    assert len(entries)==len(rows)==report['entries']==25906
    for name,key in [('corpus_prefix_statistics.py','calculator_sha256'),('run_corpus_prefixes.py','runner_sha256')]:
        assert sha((ROOT/'scripts'/name).read_bytes())==spec[key]
    seen={}
    process=subprocess.Popen(['git','-C',str(repository),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,env=env)
    try:
        for (name,oid),row in zip(entries,rows):
            assert row['file']==name and row['object_id']==oid
            if oid in seen:
                assert {k:v for k,v in row.items() if k!='file'}==seen[oid]
                continue
            process.stdin.write((oid+'\n').encode());process.stdin.flush()
            header=process.stdout.readline().split()
            assert len(header)==3 and header[0].decode()==oid and header[1]==b'blob','Missing or invalid source object'
            length=int(header[2]);raw=process.stdout.read(length)
            assert len(raw)==length and process.stdout.read(1)==b'\n'
            assert sha(raw)==row['sha256'] and length==row['bytes']
            assert hashlib.sha1(b'blob '+str(length).encode()+b'\0'+raw).hexdigest()==oid
            lengths=[]
            for match in re.finditer(r'[^ ]+',raw.decode('utf-8')):
                lengths.append(match.end()-match.start())
                if len(lengths)==2902:break
            assert row['eligible'] is (len(lengths)==2902)
            if not row['eligible']:
                assert row['statistics'] is None
            else:
                actual=row['statistics']
                assert actual['tokens']==2902 and actual['counted_units']==sum(lengths)
                assert actual['histogram']=={str(k):v for k,v in Counter(lengths).items()}
                quartiles=statistics.quantiles(lengths,n=4,method='inclusive')
                expected={'mean':statistics.mean(lengths),'sample_variance':statistics.variance(lengths),
                          'sample_std':statistics.stdev(lengths),'median':statistics.median(lengths),
                          'percentile_25':quartiles[0],'percentile_75':quartiles[2],
                          'min':min(lengths),'max':max(lengths)}
                for key,value in expected.items():
                    assert math.isclose(actual[key],value,rel_tol=1e-12,abs_tol=1e-12),(name,key)
            seen[oid]={k:v for k,v in row.items() if k!='file'}
            if len(seen)%1000==0:print(f'{len(seen)} distinct source objects checked',flush=True)
    finally:
        process.stdin.close()
        process.stdout.close()
        process.wait()
    assert process.returncode==0
    assert sum(r['eligible'] for r in rows)==report['eligible_entries']
    return {'report_sha256':sha(raw_report),'entries_checked':len(rows),
            'distinct_blobs_checked':len(seen),'eligible_entries':report['eligible_entries'],
            'method':'Pinned source bytes; regex tokenization; independent statistics-module calculation; exact histogram and duplicate-row checks; scalar tolerance 1e-12.',
            'checker_sha256':sha(Path(__file__).read_bytes())}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repository',type=Path)
    parser.add_argument('report',type=Path)
    parser.add_argument('--receipt',type=Path)
    args=parser.parse_args()
    result=check(args.repository,args.report)
    if args.receipt:
        with args.receipt.open('x',encoding='utf-8',newline='\n') as output:
            output.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
