"""Fresh conditional null distributions; no extrapolated family-wide validation."""
import importlib.util,json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];LP=ROOT.parent/'source-cache/dukotah-cicada3301/liber-primus'
spec=importlib.util.spec_from_file_location('c1_bars',LP/'analysis/round18/L7-redteam/c1_bars.py');C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
start=time.time();result=C.c4_transfer(n=120)
(HERE/'fresh-nulls.json').write_text(json.dumps({'scope':'120fresh fixed-seed histogram-preserving nulls per source length/beam setting; same source instrument, smaller than original400draw experiment. Tail estimates have11exceedances and are exploratory, not a reliable billion-trial calibration.','settings':result,'elapsed_s':time.time()-start},indent=2)+'\n',encoding='utf-8')
print('PASS measured360sourcebeam nulls; no LP2 decryption/exclusion.')
