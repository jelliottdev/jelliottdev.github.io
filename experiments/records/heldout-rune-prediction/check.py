"""Quick saved-evidence integrity/aggregation check; no external transcription or target rerun."""
import hashlib,json,math,sys
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent;R=H/'reproduction';sys.path.insert(0,str(R))
import calibration
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    public=read(H/'results.json');observed=read(R/'observed.json');bank=read(R/'null-bank/receipt.json');auth=read(R/'execution-authorization-frozen.json')
    for f,h in auth['pins'].items():assert sha(R/f)==h,f
    assert observed['authorization_sha256']==sha(R/'execution-authorization-frozen.json')
    assert observed['bank_receipt_sha256']==sha(R/'null-bank/receipt.json')
    assert bank['measurements_sha256']==sha(R/'null-bank/measurements.npz')
    with np.load(R/'null-bank/measurements.npz',allow_pickle=False) as z:
        metrics=z['metrics'];pages=z['page_loss_sums'];folds=z['fold_loss_sums']
        assert metrics.shape==(1000,26) and pages.shape==(1000,55,16) and folds.shape==(1000,2,16)
        assert np.allclose(pages.sum(axis=1)/12516,metrics[:,:16],atol=1e-10,rtol=0)
        assert np.allclose(folds.sum(axis=1)/12516,metrics[:,:16],atol=1e-10,rtol=0)
        for f in (0,1):assert np.allclose(pages[:,f::2].sum(axis=1),folds[:,f],atol=1e-6,rtol=0)
        assert calibration.compare(metrics,observed['observed']['values'],bank['tails'])==observed['comparison']
        assert np.all(metrics[:,17]==8*7928/12956)
    assert len(bank['rows'])==1000 and [x['seed'] for x in bank['rows']]==list(range(3301241024000,3301241025000))
    assert all(sum(x['monograms'])==12956 for x in bank['rows'])
    assert public['metric_count']==26 and public['marginal_flag_count']==sum(observed['comparison']['marginal_strict_1percent_flags'])==0
    cmp=observed['comparison'];assert public['family']['rank']==cmp['family_rank']==36 and public['family']['controls_at_least_as_strong']==35 and not cmp['gate']
    for j,row in enumerate(public['predictors']):
        assert row['name']==observed['names'][j] and row['bits_per_rune']==observed['observed']['values'][j]
        assert row['gain_over_uniform']==math.log2(29)-row['bits_per_rune']==observed['predictive_bits_gain_over_uniform'][j]
        assert row['nulls_at_least_as_good']==cmp['marginal_rank'][j]-1
        assert row['uniform_classification']==observed['uniform_gain_interpretation'][j]
    assert public['uniform_gain_equivalence_tolerance']==1e-10
    print('PASS: frozen pins; all1,000 saved26-metric rows, page/fold aggregation; observed calibration and public summary. No external-input recomputation performed.')
if __name__=='__main__':main()
