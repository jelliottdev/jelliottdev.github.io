"""Replay eight exact source full-book controls in a disposable source copy."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

H=Path(__file__).resolve().parent
sys.dont_write_bytecode=True


def verify(plan, source):
    for rel,expected in plan['source_files_sha256'].items():
        assert hashlib.sha256((source/rel).read_bytes()).hexdigest()==expected,rel


def canonical(rows):
    return sorted(({k:v for k,v in row.items() if k!='secs'} for row in rows),
                  key=lambda x:(x['mode'],x['wrong_key'],x['seed']))


def generate(source,nproc):
    plan=json.loads((H/'plan.json').read_text(encoding='utf-8'))
    verify(plan,source)
    with tempfile.TemporaryDirectory(prefix='liberpedia-i1-book-') as tmp:
        staged=Path(tmp)
        for rel in plan['source_files_sha256']:
            out=staged/rel
            out.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source/rel,out)
        modpath=staged/'liber-primus/analysis/round19/I1'
        sys.path.insert(0,str(modpath))
        try:
            import run_gates as gates
            gates.HERE=str(modpath)
            gates.stage_book(nproc=nproc,nseed=3,L=12956)
        finally:
            sys.path.remove(str(modpath))
        fresh=json.loads((modpath/'out_book.json').read_text(encoding='utf-8'))
    archived=json.loads((source/plan['archived_output']).read_text(encoding='utf-8'))
    assert canonical(fresh['rows'])==canonical(archived['rows'])
    return fresh


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-root',type=Path,default=H/'source')
    parser.add_argument('--nproc',type=int,default=6)
    parser.add_argument('--check',action='store_true',help='check saved rows without a new source replay')
    args=parser.parse_args()
    plan=json.loads((H/'plan.json').read_text(encoding='utf-8'))
    verify(plan,args.source_root.resolve())
    if args.check:
        import check
        check.main()
        return
    fresh=generate(args.source_root.resolve(),args.nproc)
    (H/'replayed-out_book.json').write_text(json.dumps(fresh,ensure_ascii=False,indent=2)+'\n',
                                             encoding='utf-8',newline='\n')
    import check
    check.main()


if __name__=='__main__':
    main()
