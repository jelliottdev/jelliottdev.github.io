"""Generate and evaluate the frozen synthetic reference only; never load target symbols."""
import json,hashlib,time
from pathlib import Path
import numpy as np
import engine,provenance,calibration,controls
H=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    plan=read(H/'bank-plan-frozen.json');protocol=read(H/'protocol-frozen.json')
    assert sha(H/'protocol-frozen.json')==plan['protocol_sha256']
    for p,h in plan['pins'].items():assert sha(H/p)==h,p
    out=H/'null-bank';assert not out.exists();out.mkdir();start=time.perf_counter()
    lengths=read(H/'input-shape.json')['pages'];lengths=[r['length'] for r in lengths];count=protocol['target_control_seeds']['count'];seed0=protocol['target_control_seeds']['start']
    metrics=np.empty((count,26),np.float64);page_losses=np.empty((count,55,16),np.float64);fold_losses=np.empty((count,2,16),np.float64);rows=[]
    stream_hash=hashlib.sha256()
    for j in range(count):
        seed=seed0+j;a=engine.filtered(sum(lengths),seed);r=controls.evaluate(a,lengths);stream_hash.update(a.tobytes())
        metrics[j]=r['values'];page_losses[j]=r['context']['page_loss_sums'];fold_losses[j]=[f['loss_sums'] for f in r['context']['folds']]
        rows.append(dict(replicate=j,seed=seed,stream_sha256=r['stream_sha256'],adjacent_repeats=r['adjacent_repeats'],monograms=np.bincount(a,minlength=29).tolist(),compression=r['compression']))
        if (j+1)%50==0:print('Frozen null bank',j+1,'/',count,'elapsed',round(time.perf_counter()-start,3),flush=True)
    np.savez_compressed(out/'measurements.npz',metrics=metrics,page_loss_sums=page_losses,fold_loss_sums=fold_losses)
    synthetic=read(H/'controls-results.json');tails=synthetic['tails'];checks=[]
    for group in ('negative_validation','positive'):
        for r in synthetic[group]:
            checks.append(dict(group=group,kind=r.get('kind','filtered-validation'),seed=r['seed'],stream_sha256=r['stream_sha256'],comparison=calibration.compare(metrics,r['values'],tails)))
    report=dict(stage='Null bank only; no manuscript symbols loaded/scored',bank_plan_sha256=sha(H/'bank-plan-frozen.json'),protocol_sha256=sha(H/'protocol-frozen.json'),names=synthetic['names'],tails=tails,replicates=count,rows=rows,concatenated_generated_streams_sha256=stream_hash.hexdigest(),measurements_sha256=sha(out/'measurements.npz'),synthetic_controls_sha256=sha(H/'controls-results.json'),unchanged_synthetic_recomparisons=checks,negative_joint_flags=sum(c['comparison']['gate'] for c in checks if c['group']=='negative_validation'),positive_joint_flags_by_kind={k:sum(c['comparison']['gate'] for c in checks if c['kind']==k) for k in read(H/'controls-plan-frozen.json')['plant_kinds']},seconds=time.perf_counter()-start)
    (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('Null bank complete',report['negative_joint_flags'],report['positive_joint_flags_by_kind'],round(report['seconds'],3),flush=True)
if __name__=='__main__':main()
