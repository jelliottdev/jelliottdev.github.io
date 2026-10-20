"""Recount an explicit row-major 11x11 grid and its central 5x5 perimeter."""
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

def jpeg_dimensions(raw):
    if raw[:2]!=b'\xff\xd8':raise ValueError('Not a JPEG')
    pos=2
    while pos<len(raw):
        if raw[pos]!=255:raise ValueError('Unexpected JPEG marker')
        while raw[pos]==255:pos+=1
        marker=raw[pos];pos+=1
        size=int.from_bytes(raw[pos:pos+2],'big')
        if marker in (0xc0,0xc1,0xc2):
            return [int.from_bytes(raw[pos+5:pos+7],'big'),int.from_bytes(raw[pos+3:pos+5],'big')]
        if marker in (0xda,0xd9) or size<2:break
        pos+=size
    raise ValueError('No supported frame header')

def report():
    paths=['data/index.json','text/lp2-32.txt','images/message-2016.jpg','exports/steganography/message-2016.outguess.bin']
    inputs={p:(ROOT/p).read_bytes() for p in paths}
    alpha=json.loads(inputs[paths[0]])['alphabet'];lookup={a['rune']:a for a in alpha}
    text=inputs[paths[1]].decode('utf-8')
    unknown={c for c in text if '\u16a0'<=c<='\u16ff'}-lookup.keys()
    if unknown:raise ValueError('Unknown runes')
    cells=[]
    for offset,ch in enumerate(text):
        if ch in lookup:
            i=len(cells);a=lookup[ch]
            cells.append(dict(row=i//11+1,column=i%11+1,rune_index=i,source_offset=offset,latin=a['latin'],prime=a['prime']))
    if len(cells)!=121:raise ValueError('Expected 121 runes')
    grid=[cells[i:i+11] for i in range(0,121,11)]
    def perimeter(r,c):
        return [grid[y][x] for y in range(r,r+5) for x in range(c,c+5) if y in (r,r+4) or x in (c,c+4)]
    ring=perimeter(3,3)
    windows=[dict(top_row=r+1,left_column=c+1,total=sum(x['prime'] for x in perimeter(r,c))) for r in range(7) for c in range(7)]
    return dict(input_sha256={p:hashlib.sha256(b).hexdigest() for p,b in inputs.items()},scope='LP2-32 rune-only stream in row-major 11x11 order; all runes retained; no reversal, wrap, rotation or padding.',cells=cells,row_sums=[sum(c['prime'] for c in row) for row in grid],column_sums=[sum(row[c]['prime'] for row in grid) for c in range(11)],central_perimeter=ring,central_perimeter_sum=sum(c['prime'] for c in ring),all_5x5_perimeters=windows,image_dimensions=jpeg_dimensions(inputs[paths[2]]),payload_bytes=len(inputs[paths[3]]),limitation='Arithmetic correspondence only; layout is an analytical rearrangement, not the printed line layout. No chance probability or plaintext.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args();r=report()
    if args.check:
        assert r==json.loads(Path(__file__).with_name('results.json').read_text())
        print('PASS: all grid cells, row/column sums, perimeters and file measurements')
    else:print(json.dumps(r,indent=2))
