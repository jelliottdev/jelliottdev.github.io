"""Small source-data figures with equal register styling; no raster or browser dependency."""
import argparse,html,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
R=json.loads((HERE/'results.json').read_text())
def text(x,y,s,size=16,**attrs):return '<text x="'+str(x)+'" y="'+str(y)+'" font-size="'+str(size)+'" '+ ' '.join(k.replace('_','-')+'="'+str(v)+'"' for k,v in attrs.items())+'>'+html.escape(str(s))+'</text>'
def start(title,height):return ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 '+str(height)+'" role="img" aria-label="'+html.escape(title)+'"><rect width="360" height="'+str(height)+'" fill="#fff"/><g font-family="Arial,sans-serif" fill="#24343f">',text(10,27,title,18,font_weight='bold')]
def end(parts):return ('\n'.join(parts+['</g></svg>'])+'\n').encode()
def plots():
 out={};names={'EN_KJV':'English · KJV','LP1_REAL':'English · LP1','LATIN':'Latin','OE':'Old English','DE':'German'}
 parts=start('Correct key, different text',294);parts+=[text(10,50,'Median score · 3 plants per register',15),text(350,78,'Score',15,text_anchor='end')]
 x=lambda v:130+(v+8)/5*150;cut=x(-5.5)
 parts.append('<path d="M '+str(cut)+' 85 V 244" stroke="#596b78" stroke-dasharray="4 4"/>')
 for i,row in enumerate(R['language_summary']):
  y=105+i*29;parts+=[text(10,y,names[row['register']]),'<line x1="130" x2="280" y1="'+str(y-5)+'" y2="'+str(y-5)+'" stroke="#e2e7eb"/>','<circle cx="'+str(x(row['median_score']))+'" cy="'+str(y-5)+'" r="5" fill="#285c78"/>',text(350,y,f"{row['median_score']:.2f}",text_anchor='end')]
 parts+=[text(130,260,'−8',text_anchor='middle'),text(280,260,'−3',text_anchor='middle'),text(10,284,'Dashed line: source cutoff −5.5',15)]
 out['register-scores.svg']=end(parts)
 parts=start('Score passes can miss the text',346);parts.append(text(10,50,'False pass: score passes, recovery <90%',15))
 for i,row in enumerate(R['mechanism_summary']):
  y=80+i*61;parts+=[text(10,y,row['case'].capitalize()),text(350,y,f"{row['median_recovery']*100:.1f}%",text_anchor='end'),'<rect x="10" y="'+str(y+8)+'" width="340" height="11" fill="#e5eaed"/>','<rect x="10" y="'+str(y+8)+'" width="'+str(340*row['median_recovery'])+'" height="11" fill="#285c78"/>',text(10,y+40,f"Score passes: {row['passes_score']}/7; false passes: {row['passes_score_below_90pct']}/7",14)]
 parts+=[text(10,337,'4/28 false passes · bars: median recovery',14)];out['score-recovery.svg']=end(parts)
 parts=start('Null scores depend on the setting',290);parts.append(text(10,50,'120 shuffled controls per setting',15));x=lambda v:42+(v+9)/4*300
 for i,row in enumerate(R['nulls']):
  y=80+i*63;parts.append(text(10,y,f"{row['L']} runes · beam {row['beam_w']}"));parts.append('<line x1="'+str(x(min(row['values'])))+'" x2="'+str(x(max(row['values'])))+'" y1="'+str(y+18)+'" y2="'+str(y+18)+'" stroke="#728693" stroke-width="6"/>');parts.append('<circle cx="'+str(x(row['mean']))+'" cy="'+str(y+18)+'" r="5" fill="#285c78"/>')
 for tick in [-9,-8,-7,-6,-5]:parts.append(text(x(tick),252,str(tick).replace('-','−'),text_anchor='middle'))
 parts.append(text(10,281,'Lines: observed range · dots: mean',15));out['conditional-nulls.svg']=end(parts)
 return out
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
 for name,raw in plots().items():
  if args.check:assert (HERE/name).read_bytes()==raw,name
  else:(HERE/name).write_bytes(raw)
 print('Three compact data figures verified.')
