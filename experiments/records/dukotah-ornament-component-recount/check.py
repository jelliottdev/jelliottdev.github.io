"""Independent check using only three allowlisted functions from hashed source.
No module imports, template loads, mapping loads or decoding functions execute.
"""
import ast,json
import numpy as np
from PIL import Image
from scipy import ndimage
from run import HERE,ROOT,inputs
plan=inputs()
inventory=json.loads((HERE/'source/inventory.json').read_bytes())
assert plan['boxes']==[{k:b[k] for k in ['id','page','x','y','n']} for b in inventory if b['n']<=16]
source=ast.parse((HERE/'source/reader.py').read_text(encoding='utf-8'))
names={'page_ink','labelled','comp_table'}
selected=[node for node in source.body if isinstance(node,ast.FunctionDef) and node.name in names]
assert {node.name for node in selected}==names
ns={'np':np,'Image':Image,'ndimage':ndimage,'_pagecache':{},'_labcache':{}}
exec(compile(ast.Module(body=selected,type_ignores=[]),'hashed-source-component-functions','exec'),ns)
result=json.loads((HERE/'results.json').read_bytes()); fresh={r['id']:r for r in result['rows']}
stored={r['id']:r for r in json.loads((HERE/'source/bands.json').read_bytes())}
for box in plan['boxes']:
    ct=ns['comp_table'](str(ROOT/f"images/lp2-{box['page']:02}.jpg"))
    ox=np.minimum(ct['x1'],box['x'][1])-np.maximum(ct['x0'],box['x'][0])
    oy=np.minimum(ct['y1'],box['y'][1])-np.maximum(ct['y0'],box['y'][0])
    mask=(ox>0)&(oy>0)&(ox*oy>=0.5*(ct['x1']-ct['x0'])*(ct['y1']-ct['y0']))
    components=[[int(ct[k][j]) for k in ['x0','y0','x1','y1','area']] for j in np.flatnonzero(mask)]
    assert components==fresh[box['id']]['components'],box['id']
    assert len(components)==stored[box['id']]['n_components'],box['id']
rows=list(fresh.values())
assert len(rows)==30 and len({r['page'] for r in rows})==19
assert sum(r['fresh_n_components']==r['n_reported'] for r in rows)==9
assert sum(r['fresh_n_components']>16 for r in rows)==13
# Synthetic topology/control: diagonal ink is disconnected with default 4-connectivity;
# six horizontal pixels survive min-area six, five pixels do not.
a=np.zeros((10,12),bool); a[0,0]=a[1,1]=1; a[3,0:6]=1; a[6,0:5]=1
lab,n=ndimage.label(a); assert n==4
assert sorted(np.bincount(lab.ravel())[1:].tolist())==[1,1,5,6]
assert sum(np.bincount(lab.ravel())[1:]>=6)==1
print('PASS: all 30 fresh component rectangle/area lists equal extracted pinned-source functions; 30 stored counts reproduced; topology/min-area control passed.')
