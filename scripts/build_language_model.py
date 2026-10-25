"""Build pinned GP29 rune-unit trigrams from FLORES dev only; no target scoring."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import unicodedata

ROOT=Path(__file__).resolve().parents[1]
CORPUS=ROOT/'experiments/records/parallel-languages'
ALPHABET=['F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X','S','T','B','E','M','L','NG','OE','D','A','AE','Y','IA','EA']
LANGUAGES={'eng_Latn':'English','cym_Latn':'Welsh','deu_Latn':'German','fra_Latn':'French','spa_Latn':'Spanish','ita_Latn':'Italian','por_Latn':'Portuguese','fin_Latn':'Finnish'}
ALIASES=str.maketrans({'K':'C','Q':'C','V':'U','Z':'S'})
GROUPS=('ING','TH','EO','NG','OE','AE','IA','IO','EA')

def canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')

def encode(text):
    text=''.join(c for c in unicodedata.normalize('NFD',text.upper()) if not unicodedata.category(c).startswith('M'))
    text=re.sub(r"(?<=[A-Z])['’](?=[A-Z])",'',text).translate(ALIASES)
    values=[]
    for word in re.findall('[A-Z]+',text):
        i=0
        while i<len(word):
            unit=next((g for g in GROUPS if word.startswith(g,i)),word[i]);i+=len(unit)
            values.append(ALPHABET.index({'ING':'NG','IO':'IA'}.get(unit,unit)))
    return values

def produce():
    pins=json.loads((CORPUS/'plan.json').read_text(encoding='utf-8'))['inputs']
    for item in pins:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
    models=[];sources=[]
    for language,label in LANGUAGES.items():
        path=CORPUS/(language+'.dev.txt');lines=path.read_text(encoding='utf-8').splitlines();assert len(lines)==997
        counts=Counter();runes=0
        for line in lines:
            values=encode(line);runes+=len(values)
            counts.update((a*29+b)*29+c for a,b,c in zip(values,values[1:],values[2:]))
        windows=sum(counts.values());denominator=windows+.1*29**3
        scores=[round(1000*math.log10((counts[i]+.1)/denominator)) for i in range(29**3)]
        assert all(-32768<=s<=0 for s in scores)
        models.append({'id':language,'label':label,'trainingSentences':len(lines),'trainingRunes':runes,'trainingWindows':windows,'scores':scores})
        sources.append({'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    payload={
        'schema':'liberpedia-language-model-v1','modelId':'gp29-flores-trigram-v1','scoreVersion':1,
        'alphabet':ALPHABET,'minimumRunes':40,
        'scoring':{'gramOrder':3,'index':'(a*29+b)*29+c','probability':'joint additive-smoothed trigram frequency','alpha':.1,'logBase':10,'scale':1000,'quantization':'Python round to nearest integer, ties to even; scores pinned in artifact','boundaries':'Join encoded words within each training sentence; no boundary symbols. Never join training sentences. Candidate streams use all successive supplied rune indices.'},
        'encoding':{'normalization':'Uppercase, NFD, remove Unicode combining marks. Remove straight/curly apostrophes between ASCII letters. Split at all remaining characters outside A-Z.','aliases':{'K':'C','Q':'C','V':'U','Z':'S'},'greedyUnits':list(GROUPS),'unitAliases':{'ING':'NG','IO':'IA'},'assumption':'Mechanical orthographic GP29 encoding, not phonetic transcription; discarded letters and aliases can bias language comparisons.'},
        'shuffle':{'replicates':32,'algorithm':'Fisher-Yates descending i=n-1..1; xorshift32 before every swap; swap i with state modulo (i+1).','seed':'uint32(0x33010000 XOR imul32(n,0x9e3779b1) XOR imul32(replicate+1,0x85ebca6b)); replace zero with one. replicate=0..31.','prng':'x ^= x << 13; x ^= x >>> 17; x ^= x << 5; retain uint32 after each operation.','comparison':'AtOrAbove includes ties. The identical shuffled rune streams are scored under all eight models. Modulo selection has a small finite-word bias; this is a fixed descriptive comparison, not an exact randomization p-value.'},
        'training':{'corpus':'FLORES-200','split':'dev','sentencesPerLanguage':997,'sourceArchiveSha256':'b8b0b76783024b85797e5cc75064eb83fc5288b41e9654dabc7be6ae944011f6','sources':sources,'excluded':'No LP text, devtest text, target output or calibration score enters training.'},
        'attribution':{'source':'Meta/Facebook Research FLORES-200','license':'CC-BY-SA-4.0','sourceUrl':'https://github.com/facebookresearch/flores/blob/main/flores200/README.md','licenseUrl':'https://creativecommons.org/licenses/by-sa/4.0/','changes':'Derived integer GP29 trigram statistics; encoder, smoothing and quantization specified here.'},
        'interpretation':'Scores and 32 order-shuffled comparisons are descriptive references. No winner, acceptance cutoff, language identification, probability or decryption verdict.',
        'models':models,
    }
    return {'payload':payload,'sha256':hashlib.sha256(canonical(payload)).hexdigest()}

def outputs(data):
    serialized=canonical(data).decode('utf-8')
    return {ROOT/'tools/language-model.json':serialized+'\n',ROOT/'language-model-data.js':"/* FLORES-200 derived statistics, CC BY-SA 4.0; see tools/language-model-SOURCE.txt. */\n(function(root){'use strict';const data="+serialized+";if(typeof module==='object'&&module.exports)module.exports=data;else root.RuneLanguageModelData=data;})(typeof globalThis!=='undefined'?globalThis:this);\n"}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args();data=produce()
    for path,text in outputs(data).items():
        if args.write:path.write_text(text,encoding='utf-8',newline='\n')
        else:assert path.read_text(encoding='utf-8')==text,str(path)+' is stale'
    print(json.dumps({'modelId':data['payload']['modelId'],'sha256':data['sha256'],'models':len(data['payload']['models']),'runeWindows':{m['id']:m['trainingWindows'] for m in data['payload']['models']}}))
