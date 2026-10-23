"""Small neutral SVG comparison; text remains readable at phone width."""
import argparse
import json
from pathlib import Path
from html import escape
HERE=Path(__file__).resolve().parent

def draw():
    r=json.loads((HERE/'results.json').read_bytes())
    entries=[('Archived red heading',r['header'],'#52616b'),('TEST THE KNOWLEDGE',r['phrase_th_rune'],'#286078'),('Same words; T + H separate',r['phrase_split_th'],'#80909b')]
    parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 300" role="img" aria-labelledby="title desc">', '<title id="title">The stored heading and proposed phrase have different GP sums</title>','<desc id="desc">Archived heading 786; TEST THE KNOWLEDGE 691 using one TH rune, or 768 when TH is split. These are arithmetic sums, not decoded meanings.</desc>', '<rect width="320" height="300" fill="white"/>','<g font-family="system-ui,sans-serif" fill="#20272b">','<text x="12" y="25" font-size="17" font-weight="600">What actually sums to691?</text>']
    for i,(label,item,color) in enumerate(entries):
        y=59+i*67
        parts.append(f'<text x="12" y="{y}" font-size="15">{escape(label)}</text>')
        parts.append(f'<rect x="12" y="{y+10}" width="{276*item["sum"]/786:.2f}" height="19" fill="{color}"/>')
        parts.append(f'<text x="304" y="{y}" text-anchor="end" font-size="16" font-weight="600">{item["sum"]}</text>')
        parts.append(f'<text x="12" y="{y+46}" font-size="14" fill="#58636b">{item["rune_count"]} runes</text>')
    parts+=['<text x="12" y="270" font-size="14">691 matches the phrase.</text><text x="12" y="289" font-size="14">It does not match this stored heading.</text>','</g></svg>']
    return ''.join(parts).replace('to691','to 691')+'\n'

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();p=HERE/'red-sums.svg';s=draw()
    if args.check:assert p.read_text(encoding='utf-8')==s
    else:p.write_text(s,encoding='utf-8',newline='\n')
