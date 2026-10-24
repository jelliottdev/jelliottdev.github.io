"""Additional small exact-source function replays, no model search."""
import ast,collections,hashlib,json,os,subprocess,types
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
M=json.loads((HERE/'source-manifest.json').read_text())['sources']
def read(suffix):return (ROOT/next(v['path'] for k,v in M.items() if k.endswith(suffix))).read_text(encoding='utf-8')
def load_functions(suffix,names,globals):
 tree=ast.parse(read(suffix));tree.body=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
 assert len(tree.body)==len(names);exec(compile(tree,suffix,'exec'),globals);return globals
c=load_functions('round19/R1/c_prior.py',{'jpeg_vector'},{'hashlib':hashlib})
original=ROOT/'images/lp2-00.jpg';im=Image.open(original);icc=im.info['icc_profile'];outputs={}
for name,gray in [('pil-keep',False),('pil-gray',True)]:
 target=HERE/(name+'.jpg')
 if gray:im.convert('L').save(target,'JPEG',quality=92,optimize=True,icc_profile=icc)
 else:im.save(target,'JPEG',quality='keep',optimize=True,icc_profile=icc)
 outputs[name]={'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'vector':c['jpeg_vector'](str(target))}
observed=c['jpeg_vector'](str(original))
assert all(outputs['pil-keep']['vector'][key]==observed[key] for key in ['ncomp','sampling','huff','icc_len','icc_md5','dqt_sha1'])
gray=outputs['pil-gray']['vector'];assert gray['ncomp']==1 and gray['sampling']=='11' and gray['dqt_sha1']==observed['dqt_sha1'][:1] and gray['huff']==observed['huff'] and gray['icc_md5']==observed['icc_md5']
# Recount saved-candidate reach with the exact source function on pinned-checkout data.
read_files=[]
def tracked_open(path,*args,**kwargs):
 p=Path(path);raw=p.read_bytes();read_files.append({'path':str(p.resolve()),'sha256':hashlib.sha256(raw).hexdigest(),'git_object':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()});return open(path,*args,**kwargs)
repo=ROOT.parent/'source-cache/dukotah-cicada3301'
d=load_functions('round19/R1/d_budget.py',{'s2_reach'},{'os':os,'json':json,'open':tracked_open,'LP':str(repo/'liber-primus')})
recount=d['s2_reach']()
saved=json.loads(read('round19/R1/out_d.json'))['D_c']
assert recount['detail']==saved['detail']
comparison={'saved_total':saved['stored_rows_total_est'],'observed_total':recount['stored_rows_total_est'],'equal':recount==saved,'scope':'Same exact source function on current pinned checkout; missing saved working-tree rows are not recreated.'}
# Every file actually consumed is compared with its pinned Git object ID.
raw=subprocess.check_output(['git','-C',str(repo),'ls-tree','-r','f08b20b632d91209ddbaa747e8e2f23df0c78ba1','--','liber-primus/analysis/round13/B04/','liber-primus/analysis/round16/prng/','liber-primus/analysis/round17/'])
tree={line.split('\t')[1]:line.split()[2] for line in raw.decode().splitlines()}
for row in read_files:
 row['source_path']=Path(row['path']).relative_to(repo.resolve()).as_posix()
 raw=Path(row['path']).read_bytes();normal=raw.replace(b'\r\n',b'\n');normalized_oid=hashlib.sha1(b'blob '+str(len(normal)).encode()+b'\0'+normal).hexdigest()
 row['pinned_tree_relation']='exact' if tree.get(row['source_path'])==row['git_object'] else 'CRLF-equivalent' if tree.get(row['source_path'])==normalized_oid else 'not-matched'
 assert row['pinned_tree_relation']!='not-matched',row
result={'jpeg_counterexample':{'source_original_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'observed':observed,'reencoded':outputs,'covered':'Re-encode same observed JPEG through Pillow, retaining DQT/sampling/ICC with optimized Huffman, plus explicit grayscale counterpart.','not_covered':'No original PDF or Ghostscript render recovered; no unique historical producer inference.'},'source_s2_reach_recount':recount,'saved_recount_comparison':comparison,'pinned_recount_inputs':read_files}
(HERE/'finite-checks-results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('Pillow RGB/gray metadata alternatives PASS; source s2_reach recount:',recount['stored_rows_total_est'],'retained rows vs saved',saved['stored_rows_total_est'],'across',len(read_files),'pinned input reads.')
