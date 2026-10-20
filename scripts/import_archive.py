import json, hashlib, shutil, sys
from pathlib import Path
from collections import Counter
from PIL import Image, ImageChops

source = Path(sys.argv[1])
dest = Path(sys.argv[2])
def read(name): return json.loads((source/name).read_text(encoding='utf-8'))
def write(name,obj):
    p=dest/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
def copy(name,target):
    p=dest/target;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,p)
alphabet=read('corpus/gematria-primus.json')['symbols']
am={a['rune']:a for a in alphabet}
pages=read('corpus/page-index.json')
reviews={p['page']:p for p in read('corpus/rune-review/current-LP2-reviewed-mark-profile-v1.json')['changed_pages']}
features=read('corpus/rune-review/visual-features.json')
solved={}
for c in read('solutions/current-solved-reading-v1.json')['controls']:
    for d in c.get('decoded_pages',[]):
        solved[d['page']]={'literal':d['literal_transliteration'],'method':c['method'],'section':c['id'],'section_pages':c['pages'],'reading':c['reading']}
source_records=[]
for s in read('metadata/site-snapshots.json'):
    if s.get('status')=='saved':
        source_records.append({k:s[k] for k in ['url','retrieved_at','sha256'] if k in s})
records=[]
for p in pages:
    pid=p['id'];image=source/p['image_path']
    assert hashlib.sha256(image.read_bytes()).hexdigest()==p['image_sha256']
    copy(p['image_path'],f'images/{pid}.jpg')
    im=Image.open(image).convert('RGB'); mask=ImageChops.difference(im,Image.new('RGB',im.size,'white')).convert('L').point(lambda v:255 if v>80 else 0)
    box=mask.getbbox() or (0,0,*im.size)
    thumb=im.crop(box);thumb.thumbnail((360,480));(dest/'thumbs').mkdir(exist_ok=True);thumb.save(dest/f'thumbs/{pid}.jpg',quality=82)
    text=(source/p['transcription_path']).read_text(encoding='utf-8') if p.get('transcription_path') else ''
    if text: copy(p['transcription_path'],f'text/{pid}.txt')
    tokens=[am[c] for c in text if c in am]
    freqs=Counter(c['rune'] for c in tokens)
    lines=[]
    for line in text.splitlines():
        if not line.strip() or line.strip() in ['&','$','§','%']:continue
        letters=[am[c] for c in line if c in am]
        lines.append({'raw':line,'latin':''.join(am[c]['latin'] if c in am else c for c in line),'runes':len(letters),'prime_sum':sum(c['prime'] for c in letters)})
    visual={'glyphs':[{k:g[k] for k in ['ordinal','rectangle','master_rune','ink_class']} for g in features['glyphs'] if g['page']==pid],
            'punctuation':[{k:g[k] for k in ['source_line','rectangle','component_count','ink_class']} for g in features['punctuation'] if g['page']==pid]}
    review=reviews.get(pid)
    corrections=[]
    if review: corrections=[{'start':e['start'],'end':e['end'],'old':e['old'],'new':e['new'],'note':e.get('meaning','Documented visual punctuation correction.')} for e in review['edits']]
    if pid=='lp1-10':corrections.append({'note':'The native-image review reads BELIEUE (contextual English: BELIEVE); the archived transcription swaps I/E at zero-based rune positions 116–117. The known reading below uses the reviewed correction.'})
    record={k:p[k] for k in ['id','release','release_index','kind','status','status_basis','image_sha256','image_dimensions','rune_count']}
    record.update({'title':p.get('title',''),'lines':lines,'raw':text,'frequencies':dict(freqs),'prime_sum':sum(t['prime'] for t in tokens),
        'sources':[{'name':m['source'],'url':m['source_url'],'commit':m['commit']} for m in p['mirrors']],
        'visual':visual,'corrections':corrections,'reviewed_text':review['effective_text'] if review else None,'reading':solved.get(pid),
        'notes':[],'transcription_sha256':hashlib.sha256((source/p['transcription_path']).read_bytes()).hexdigest() if p.get('transcription_path') else None})
    if pid=='lp1-10':
        chars=list(text); positions=[i for i,c in enumerate(chars) if c in am]
        a,b=positions[116:118]; chars[a],chars[b]=chars[b],chars[a]
        record['reviewed_text']=''.join(chars)
    if pid=='lp2-15':
        panel=read('corpus/decimal-panels/lp2-15-v1.json')
        record['numbers']=panel['values']
        record['notes']=[{'title':'Decimal panel','text':'Sixteen decimal numbers appear in four rows and four columns. 3299 is the only red entry; 708 is the only three-digit entry.','rect':panel['panel_rectangle']},
        {'title':'Open-loop drawing','text':'Below the number panel are two open lobes with a crossing, resembling an infinity sign. Visible gaps remain in the drawing. Its intended meaning is not established.','rect':[850,1490,580,210]},
        {'title':'Header','text':'The red header contains nine runes in groups of four and five: F U L M / A EA Y OE A. Latin labels are transliterations, not plaintext.','rect':[900,650,600,150]}]
    if visual['glyphs']:
        reds=sum(g['ink_class']=='red' for g in visual['glyphs'])
        record['notes'].append({'title':'Recorded ink colors','text':f'The stored visual survey classifies {reds} rune regions as red and {len(visual["glyphs"])-reds} as dark. These are measurements of the reviewed image regions, not interpretations of the colors.'})
    if pid=='lp2-00':record['notes'].append({'title':'Oversized opening rune','text':'The opening S rune extends alongside the first three text rows. Its rectangle is recorded separately from the ordinary first-row glyphs.','rect':[599,664,153,501]})
    if pid=='lp2-01':record['notes'].append({'title':'Touching glyphs','text':'The recorded tenth visual row contains C/OE glyphs that touch at their feet. Overlapping inspection regions preserve their context.'})
    write(f'data/pages/{pid}.json',record)
    records.append({k:record[k] for k in ['id','release','release_index','kind','status','status_basis','title','rune_count','prime_sum']} | {'search':record['raw']+' '+ ' '.join(l['latin'] for l in lines)+' '+(record['reading']['reading'] if record['reading'] else ''),'has_notes':bool(record['notes']),'has_reading':bool(record['reading'])})
write('data/index.json',{'pages':records,'alphabet':alphabet,'sources':source_records,'snapshot':'2026-10-05','compiled':'2026-10-19','transcriptions':sum(bool(p.get('transcription_path')) for p in pages)})
for name in ['corpus/rune-review/source-correction-registry-v1.json','corpus/rune-review/current-LP2-reviewed-mark-profile-v1.json','corpus/decimal-panels/lp2-15-v1.json']:
    copy(name,'data/evidence/'+Path(name).name)
write('data/manifest.json',{'images':{p['id']:p['image_sha256'] for p in pages},'source_commits':{m['source']:m['commit'] for m in pages[0]['mirrors']},'excludes':['Experimental cipher runs','Unverified theories','Private research conversations'],'notes':'Image copies verified against source SHA-256. Thumbnails are cropped derivatives. Transcriptions retain archive conventions; documented corrections are separately exposed.'})
print(f'Built {len(pages)} pages, {len(source_records)} source references, {len(solved)} known page readings.')

reading_source=source/'solutions/current-solved-reading-v1.json'
reading_record=read('solutions/current-solved-reading-v1.json')
write('data/evidence/known-readings.json',{'schema':'wiki-known-readings-v1','source_record':'solutions/current-solved-reading-v1.json','source_sha256':hashlib.sha256(reading_source.read_bytes()).hexdigest(),'compiled_utc':reading_record['created_utc'],'scope':reading_record['scope'],'note':'Extracted known readings and recorded methods, not experimental cipher outputs. Contextual English and literal transliteration are distinct representations. This extract is not a fresh photographic audit.','controls':[{k:c[k] for k in ['id','pages','method','reading','corrections','decoded_pages']} for c in reading_record['controls']]})

# Search summaries and source filename cross-reference.
index=json.loads((dest/'data/index.json').read_text(encoding='utf-8'))
originals={p['id']:p for p in pages}
for item in index['pages']:
    p=json.loads((dest/f"data/pages/{item['id']}.json").read_text(encoding='utf-8'))
    item.update({'combined_index':originals[item['id']]['combined_index'],'source_names':[{'name':m['source'],'filename':m['source_url'].rsplit('/',1)[1],'url':m['source_url']} for m in originals[item['id']]['mirrors']],'correction_count':len(p['corrections']),'section':p['reading']['section'] if p['reading'] else None,'method':p['reading']['method'] if p['reading'] else None,'notes_text':' '.join(n['title']+' '+n['text'] for n in p['notes']),'correction_text':' '.join(c['note'] for c in p['corrections']),'literal':p['reading']['literal'] if p['reading'] else ''})
    item['text_rows']=[{'row':i+1,'raw':l['raw'],'latin':l['latin']} for i,l in enumerate(p['lines'])]
    item['contextual']=p['reading']['reading'] if p['reading'] else ''
    item['transcription_search']=p['raw']+' '+' '.join(l['latin'] for l in p['lines'])
    item['search']+=' '+item['notes_text']+' '+item['correction_text']+' '+(item['section'] or '')+' '+(item['method'] or '')
write('data/index.json',index)

method_source=source/'solutions/known-controls.json'
method_record=read('solutions/known-controls.json')
write('data/evidence/reading-methods.json',{'source_sha256':hashlib.sha256(method_source.read_bytes()).hexdigest(),'scope':method_record['scope'],'interruption_provenance':method_record['interruption_provenance'],'walkthrough_url':'https://github.com/scream314/cicada3301/blob/10733feb487bb8beb9966d534727ee5897aa54fc/liber_primus.md','controls':[{k:c[k] for k in ['id','pages','method','key','skip','start','shift','boundary']} for c in method_record['controls']]})

# Recompute the shipped mathematical article evidence after rebuilding page data.
import runpy
runpy.run_path(str(Path(__file__).with_name("build_numeric_notes.py")),run_name="__main__",init_globals={"OUTPUT_ROOT":dest})

runpy.run_path(str(Path(__file__).with_name("build_page_notes.py")),run_name="__main__",init_globals={"OUTPUT_ROOT":dest})

runpy.run_path(str(Path(__file__).with_name("build_access_exports.py")),run_name="__main__",init_globals={"OUTPUT_ROOT":dest})
