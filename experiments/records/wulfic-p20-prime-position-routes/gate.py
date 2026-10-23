"""Pre-outcome source-script parity and recoverable planted column-route control."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import runpy
import subprocess
import tempfile
from pathlib import Path

from engine import ioc, is_prime, source_stage

HERE = Path(__file__).resolve().parent
COMMIT = "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"


def git_bytes(root: Path, path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), "show", f"{COMMIT}:{path}"])


def staged_source(root: Path, page_bytes: bytes) -> tuple[dict, str]:
    source = git_bytes(root, "tools/legacy/solve_p20.py")
    poem = git_bytes(root, "data/corpora/deor_poem.txt")
    assert subprocess.check_output(["git", "-C", str(root), "hash-object", "--stdin"],input=source).decode().strip() == "05a7d226dab2ffb4ad3f324039ae0c8d56e639ab"
    with tempfile.TemporaryDirectory() as temp:
        folder=Path(temp)/"tools"
        for p in (folder/"legacy",folder/"pages"/"page_20",folder/"data"):
            p.mkdir(parents=True,exist_ok=True)
        script=folder/"legacy"/"solve_p20.py"
        script.write_bytes(source)
        (folder/"pages"/"page_20"/"runes.txt").write_bytes(page_bytes)
        (folder/"data"/"deor_poem.txt").write_bytes(poem)
        printed=io.StringIO()
        with contextlib.redirect_stdout(printed):
            variables=runpy.run_path(str(script),run_name="source_replay")
        return variables,printed.getvalue()


def build(root: Path) -> dict:
    assert len([i for i in range(217) if is_prime(i)]) == 47
    assert len([i for i in range(217) if not is_prime(i)]) == 170
    target=([16,8,18]*57)[:170]  # many literal THE trigrams in source Runeglish
    column_order=[i for col in range(2) for i in range(col,170,2)]
    nonprime=[0]*170
    for pos,source_position in enumerate(column_order):
        nonprime[source_position]=target[pos]
    values=[]; cursor=0
    for pos in range(217):
        if is_prime(pos):
            values.append(0)
        else:
            values.append(nonprime[cursor]); cursor+=1
    page_bytes=''.join(RUNES[x] for x in values).encode('utf8')
    poem=git_bytes(root,"data/corpora/deor_poem.txt")
    deor=[ord(c)-ord('a') for c in poem.decode('utf8').lower() if c.isalpha()]
    ours=source_stage(values,deor)
    assert ours['best_shift']==0
    assert len(set(ours['shift_iocs']))==1
    col=next(r for r in ours['routes'] if r['name']=='columnar_w2')
    assert col['values']==target and col['trigrams']>5 and col['reported']
    assert all(abs(ioc([(x-s)%29 for x in nonprime])-ioc(nonprime))<1e-12 for s in range(29))
    assert all(abs(r['ioc']-ioc(nonprime))<1e-12 for r in ours['routes'] if r['complete_permutation'])
    source,printed=staged_source(root,page_bytes)
    observed={name:(value,info) for name,value,info in source['results']}
    retained=[r for r in ours['routes'] if r['reported']]
    assert set(observed)=={r['name'] for r in retained}
    for route in retained:
        assert abs(observed[route['name']][0]-route['ioc'])<1e-12
    assert source['total']==217 and source['best_shift']==0
    assert source['np_plain']==nonprime
    return {'schema':'wulfic-p20-route-gate-v1','source_commit':COMMIT,
            'source_script_blob':'05a7d226dab2ffb4ad3f324039ae0c8d56e639ab',
            'synthetic_page_sha256':hashlib.sha256(page_bytes).hexdigest(),
            'synthetic_planted_170_rune_column_recovery':True,
            'source_retained_route_parity_count':len(retained),
            'all_caesar_shifts_ioc_equal':True,
            'all_complete_permutation_iocs_equal':True,
            'source_script_unmodified':True,
            'source_stdout_sha256':hashlib.sha256(printed.encode('utf8')).hexdigest()}


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=build(args.source_root)
    raw=json.dumps(result,indent=2).encode('utf8')+b'\n'
    target=HERE/'gate.json'
    if args.check:
        assert target.read_bytes()==raw
    else:
        target.write_bytes(raw)
    print('Pinned source parity and planted route gate passed.')


if __name__=='__main__':
    main()
