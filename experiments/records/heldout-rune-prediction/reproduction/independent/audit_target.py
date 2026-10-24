"""Independent complete target reconstruction; no producer scorer is imported."""
import sys, argparse, ast, hashlib, json, lzma, math, time
from pathlib import Path
sys.dont_write_bytecode = True
import numpy as np
import oracle as O
from check_calibration_provenance import scalar, provenance_scalar

read = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def run(root):
    started = time.perf_counter()
    observed = read(root/'observed.json'); authorization = read(root/'execution-authorization-frozen.json')
    for path, digest in authorization['pins'].items():
        assert sha(root/path) == digest, path
    assert observed['authorization_sha256'] == sha(root/'execution-authorization-frozen.json')
    assert observed['protocol_sha256'] == sha(root/'protocol-frozen.json')
    bank = read(root/'null-bank/receipt.json')
    assert observed['bank_receipt_sha256'] == sha(root/'null-bank/receipt.json')
    assert sha(root/'null-bank/measurements.npz') == bank['measurements_sha256']
    manifest = read(root/'source-inputs.json')
    for row in manifest['files']:
        path = root/'source'/row['path']
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], str(path)
    tree = ast.parse((root/'source/liber-primus/src/lp/gematria.py').read_text(encoding='utf8'))
    table = ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='GEMATRIA' for t in n.targets)))
    alphabet = {r[1]:i for i,r in enumerate(table)}
    segments = (root/'source/liber-primus/data/krisyotam_runes.txt').read_text(encoding='utf8').split('%')
    assert len(segments) == 57
    pages = [[alphabet[c] for c in s if c in alphabet] for s in segments[:55]]
    shape = read(root/'input-shape.json')
    for i,(page,row) in enumerate(zip(pages,shape['pages'])):
        assert row['source_segment']==i and len(page)==row['length']
        assert hashlib.sha256(bytes(page)).hexdigest()==row['indices_sha256']
    values = sum(pages,[]); n = len(values); positions = sum(len(p)-8 for p in pages)
    assert n==12956 and positions==12516
    assert hashlib.sha256(bytes(values)).hexdigest()==shape['stream_sha256']==observed['source_stream_sha256']==observed['observed']['stream_sha256']
    sums = np.zeros((55,16)); folds=[]
    for fold in (0,1):
        model = O.fit([p for i,p in enumerate(pages) if i%2!=fold],8)
        for i,page in enumerate(pages):
            if i%2!=fold: continue
            for j,(kind,k) in enumerate((kind,k) for kind in ('kt','ppm') for k in range(1,9)):
                sums[i,j]=O.score([page],model,kind,k,8)['total_bits']
        folds.append(sums[fold::2].sum(axis=0))
    result=observed['observed']; context=result['context']
    page_error=float(np.max(np.abs(sums-np.asarray(context['page_loss_sums'])))); assert page_error<1e-6
    rates=sums.sum(axis=0)/positions
    rate_error=float(np.max(np.abs(rates-np.asarray(result['values'][:16])))); assert rate_error<1e-10
    fold_error=0.
    for i,row in enumerate(context['folds']):
        assert row['test_parity']==i and row['scored_positions']==sum(len(p)-8 for j,p in enumerate(pages) if j%2==i)
        fold_error=max(fold_error,float(np.max(np.abs(folds[i]-np.asarray(row['loss_sums'])))))
    assert fold_error<1e-6 and context['scored_positions']==positions==observed['scored_positions']
    integer=0
    for x in values: integer=integer*29+x
    packed=integer.to_bytes((integer.bit_length()+7)//8,'big')
    compression=[]
    for mode,data in [('raw1',bytes(values)),('packed',packed)]:
        size=len(lzma.compress(data,preset=9|lzma.PRESET_EXTREME)); row=result['compression'][mode]
        assert len(data)==row['input_bytes'] and size==row['compressed_bytes'] and 8*size/n==row['bits_per_rune']
        compression.append(8*size/n)
    provenance=provenance_scalar(values,(29,58,116,232,464))
    provenance_error=float(np.max(np.abs(np.asarray(provenance)-np.asarray(result['values'][18:])))); assert provenance_error<1e-8
    reconstructed=list(rates)+compression+list(provenance)
    with np.load(root/'null-bank/measurements.npz',allow_pickle=False) as arrays: refs=arrays['metrics'].tolist()
    tails=['lower']*23+['upper']*3
    assert observed['tails']==bank['tails']==tails and observed['names']==bank['names']
    scores,rank,constants=scalar(refs+[result['values']],tails); cmp=observed['comparison']
    assert rank==cmp['family_rank'] and rank/1001==cmp['family_rank_fraction'] and cmp['family_reference_rows']==1001 and constants==cmp['constant_metrics']
    z_error=max(abs(x-y) for x,y in zip(scores,cmp['reference_max_z']+[cmp['max_z']])); assert z_error<1e-6
    flags=[]; ranks=[]
    for j,tail in enumerate(tails):
        sign=-1 if tail=='lower' else 1; column=sorted(r[j]*sign for r in refs); value=result['values'][j]*sign
        ranks.append(1+sum(x>=value for x in column)); at=.99*999; lo=math.floor(at); threshold=column[lo]+(at-lo)*(column[lo+1]-column[lo]); flags.append(value>threshold)
    assert ranks==cmp['marginal_rank'] and flags==cmp['marginal_strict_1percent_flags']
    assert [r/1001 for r in ranks]==cmp['marginal_reference_fraction']
    assert cmp['gate']==(rank/1001<.01 and any(flags))
    tolerance=read(root/'reporting-tolerance-addendum-frozen.json')['absolute_bits_per_rune_tolerance']
    gains=[math.log2(29)-x for x in result['values'][:16]]
    assert gains==observed['predictive_bits_gain_over_uniform'] and observed['uniform_bits_per_rune']==math.log2(29)
    labels=['better' if g>tolerance else 'worse' if g< -tolerance else 'equivalent' for g in gains]
    assert labels==observed['uniform_gain_interpretation'] and tolerance==observed['uniform_gain_equivalence_tolerance']
    assert sum(a==b for a,b in zip(values,values[1:]))==result['adjacent_repeats']
    return dict(status='PASS',observed_sha256=sha(root/'observed.json'),authorization_sha256=sha(root/'execution-authorization-frozen.json'),audit_script_sha256=sha(Path(__file__)),oracle_sha256=sha(Path(__file__).with_name('oracle.py')),source_stream_sha256=shape['stream_sha256'],source_segments=55,scored_positions=positions,all_target_predictive_profiles_checked=16,all_page_loss_cells_checked=55*16,maximum_page_loss_error=page_error,maximum_fold_loss_error=fold_error,maximum_predictive_rate_error=rate_error,all_lzma_modes_checked=2,all_provenance_metrics_checked=8,maximum_provenance_error=provenance_error,maximum_scalar_vector_z_error=z_error,family_rank=rank,family_reference_rows=1001,gate=cmp['gate'],marginal_flags=flags,uniform_gain=gains,uniform_gain_interpretation=labels,limits='Complete target reconstruction; reference metric bank is reused with prior independent audit. Conditional finite comparison, not an OTP, randomness, plaintext or cipher-family verdict. Packed LZMA lacked planted power.',seconds=time.perf_counter()-started)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--producer-root',required=True,type=Path);p.add_argument('--output',type=Path);p.add_argument('--check-only',action='store_true');a=p.parse_args()
    assert a.check_only or a.output, 'Choose --check-only or a fresh --output'
    if a.output: assert not a.output.exists(),'Refusing overwrite'
    result=run(a.producer_root)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
