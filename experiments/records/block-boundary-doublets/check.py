"""Independent direct scan of page-anchored LP2 block-boundary events."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
data=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
alphabet={row['rune'] for row in json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']}
positions=[]
for number in range(56):
    stream=[c for c in (ROOT/f'text/lp2-{number:02d}.txt').read_text(encoding='utf-8') if c in alphabet]
    positions.extend((number,i) for i in range(1,len(stream)) if stream[i-1]==stream[i])
assert len(positions)==86
assert sum(row['edges'] for row in data['pages'])==12901
for item in data['fixed_phase_zero']:
    assert item['matches']==sum(position%item['size']==0 for _,position in positions)
assert data['top_by_z'][0]['matches']==sum(position%12==8 for _,position in positions)
assert data['candidate_count']==sum(range(2,30))
print('PASS: independent page scan, 86 event positions and fixed block sizes')
