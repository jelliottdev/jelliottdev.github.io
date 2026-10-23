"""Reconstruct LP2-54–55 words directly from the two page transcriptions."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
words=[]; current=''; start_page=None
for number in (54,55):
    page=f'lp2-{number:02}'
    for char in (ROOT/f'text/{page}.txt').read_text(encoding='utf-8'):
        if '\u16a0' <= char <= '\u16ff':
            if not current: start_page=page
            current+=char
        elif char in '-.':
            if current:
                words.append((current,start_page));current='';start_page=None
if current:words.append((current,start_page))
saved=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
assert len(words)==saved['original_words']==66
assert [len(x[0]) for x in words[:2]]==[1,8]
assert len(words[2:])==64
assert [len(x[0]) for x in words[2:]]==[y['rune_length'] for y in saved['grid']]
assert [x[1] for x in words[2:]]==[y['page_of_start'] for y in saved['grid']]
assert sum(x[1]=='lp2-54' for x in words[2:])==48
assert sum(x[1]=='lp2-55' for x in words[2:])==16
assert len({tuple(y['cell_order']) for y in saved['spiral_routes']})==8
assert all(sorted(y['cell_order'])==list(range(1,65)) for y in saved['spiral_routes'])
print('PASS independent lp2-54-55-word-square recount')
