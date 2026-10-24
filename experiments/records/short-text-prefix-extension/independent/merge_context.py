"""Compose old84/new short-text results only after exact old/new pattern-array comparison."""
import sys,json,argparse,ast,importlib.util,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np
import direct as D
H=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_bytes())

def merge(root,results,inputs,baseline):
    manifest=read(root/'inputs-frozen.json');old=baseline/'reproduction'
    assert D.sha((root/'inputs-frozen.json').read_bytes())==D.sha((old/'inputs-frozen.json').read_bytes())
    for row in manifest['source_files']:assert D.sha((old/'source'/row['path']).read_bytes())==D.sha((root/'source'/row['path']).read_bytes())==row['sha256']
    assert D.sha((old/'replay.py').read_bytes())==read(old/'target-plan-frozen.json')['runner_sha256']
    assert D.sha((old/'scan_results.json').read_bytes())==read(old/'independent-target-audit.json')['output_sha256']
    lpraw=(inputs/manifest['manuscript']['path']).read_bytes();assert D.sha(lpraw)==manifest['manuscript']['sha256']
    obs,fc=D.manuscript(lpraw,root/'source/liber-primus/src/lp/gematria.py');newpatterns=D.patterns(obs,fc)
    # Execute only the original frozen replay audit's array-construction statements.
    # verify() has no data dependency here: its C return is unused until later.
    # Stop before reading results and before any target/winner loop.
    sourcepath=old/'source/liber-primus/analysis/round10/L4-skeleton/skel.py'
    spec=importlib.util.spec_from_file_location('original_saved_skel',sourcepath);sk=importlib.util.module_from_spec(spec);spec.loader.exec_module(sk);sk.ROOT=str(inputs/'liber-primus')
    tree=ast.parse((old/'replay.py').read_text(encoding='utf-8'));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='audit');body=[]
    for node in fn.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='results' for t in node.targets):break
        body.append(node)
    assert len(body)==7 and all(isinstance(n,(ast.Assign,ast.For)) for n in body)
    namespace={'verify':lambda:{},'skel':sk,'np':np}
    exec(compile(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])),str(old/'replay.py')+'#pattern-construction','exec'),namespace)
    original=namespace['patterns'];pattern_checks=[]
    for name,(o,f) in newpatterns.items():
        oo,ff,mode=original[name];assert mode=='interval' and np.array_equal(o,oo) and np.array_equal(f,ff)
        pattern_checks.append(dict(pattern=name,width=len(o),observed_sha256=D.ah(o),fcounts_sha256=D.ah(f),exact_arrays_equal=True))
    oldscores=read(old/'scan_results.json');new=read(results/'results.json');p=read(root/'protocol-frozen.json');rows=[]
    original_names={r['name'] for r in manifest['corpus'] if r['words']>=2928}
    for group in new['groups']:
        w=group['width'];added={r['name'] for r in p['selected'][str(w)]};assert not original_names&added
        expected_total={r['name'] for r in manifest['corpus'] if r['words']>=w};assert original_names|added==expected_total
        for name,newbest in group['best'].items():
            assert set(oldscores['per_text'][name])==original_names
            oldbest=oldscores['best'][name];choices=[dict(**oldbest,provenance='reused original84'),dict(**newbest,provenance='new short-text scan')]
            # Exact raw equality resolves by original sorted text order.
            winner=sorted(choices,key=lambda r:(-r['count'],r['text']))[0]
            starts_old=sum(r['words']-w+1 for r in manifest['corpus'] if r['name'] in original_names)
            starts_new=sum(r['starts'] for r in p['selected'][str(w)])
            assert starts_old+starts_new==sum(r['words']-w+1 for r in manifest['corpus'] if r['words']>=w)
            rows.append(dict(pattern=name,width=w,old_texts=84,new_texts=len(added),total_texts=len(expected_total),old_alignment_starts=starts_old,new_alignment_starts=starts_new,total_alignment_starts=starts_old+starts_new,old_best=oldbest,new_best=newbest,merged_best=winner,new_improves_old_raw_maximum=newbest['count']>oldbest['count']))
    return dict(schema='c01-short-prefix-merged-context-v1',merge_script_sha256=D.sha((H/'merge_context.py').read_bytes()),protocol_sha256=D.sha((root/'protocol-frozen.json').read_bytes()),new_results_sha256=D.sha((results/'results.json').read_bytes()),old_results_sha256=D.sha((old/'scan_results.json').read_bytes()),old_runner_sha256=D.sha((old/'replay.py').read_bytes()),pattern_arrays_compared=pattern_checks,rows=rows,any_new_improves_old_maximum=any(r['new_improves_old_raw_maximum'] for r in rows),method='Reused original84saved maxima plus independently audited new rows; six exact arrays compared against construction in original frozen replay. Corpus validation and pattern reconstruction only; no original84 target scan rerun.',limits='Merged coverage concerns only the six fixed interval prefixes under identical normalization; no historical224corpus, all-subwindow, probability or plaintext claim.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--run-root',required=True,type=Path);p.add_argument('--result-root',required=True,type=Path);p.add_argument('--inputs-root',required=True,type=Path);p.add_argument('--baseline-root',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();assert not a.output.exists()
    r=merge(a.run_root.resolve(),a.result_root.resolve(),a.inputs_root.resolve(),a.baseline_root.resolve());a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main()
