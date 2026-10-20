"""Draw one actual lookup from the saved control trace."""
import json
from html import escape
from pathlib import Path
HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
first=r['result']['trace'][0];p,s,w,l=map(int,first['entry'].split(':'))
steps=[(f'Paragraph {p}', 'Count from the first prose paragraph'),(f'Sentence {s}', 'Use the declared punctuation rule'),(f'Word {w}: '+first['word'],'Count words in that sentence'),(f'Letter {l}: '+first['character'],'Count ASCII letters inside the word')]
parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 420" role="img" aria-labelledby="title desc"><title id="title">First actual Emerson lookup</title><desc id="desc">Coordinate 1:2:3:1 selects paragraph one, sentence two, word three, always, and its first letter a.</desc><rect width="360" height="420" fill="#faf9f5"/><g font-family="sans-serif" fill="#243c48"><text x="20" y="32" font-size="20">First lookup: '+escape(first['entry'])+'</text>']
for i,(title,note) in enumerate(steps):
    y=78+i*75
    parts.append(f'<text x="20" y="{y}" font-size="18">{escape(title)}</text><text x="20" y="{y+24}" font-size="13">{escape(note)}</text>')
    if i<3:parts.append(f'<path d="M25 {y+34} v18 m-4 -4 l4 4 4 -4" stroke="#416879" fill="none"/>')
parts.append('<path d="M20 352 H340" stroke="#bec8ca"/><text x="20" y="377" font-size="13">15 lookups + 7 literal characters = 22 outputs</text><text x="20" y="400" font-size="13">Historical control, not a new decipherment.</text></g></svg>')
(HERE/'lookup.svg').write_text(''.join(parts)+'\n',encoding='utf-8',newline='\n')
