"""Replay known-English language controls and chart. Standard library, offline."""
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/'scripts'))
from known_reading_language_control import calculate


def figure(report):
    labels=['Warning','Welcome','Some wisdom','First koan','Loss of divinity','Second koan','Instruction','LP2-56','LP2-57','Pooled']
    modes=['derived-letters / letters','derived-gp-length / gp-length','native-runes / gp-length']
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="360" height="525" viewBox="0 0 360 525" role="img" aria-labelledby="t d">',
         '<title id="t">Nearest language for known English readings</title>',
         '<desc id="d">All source sections have established English readings. Nearest statistical matches sometimes name other languages, depending on section and units. The pooled text matches English in all columns. All languages have the same styling.</desc>',
         '<rect width="360" height="525" fill="#faf9f5"/><g fill="#263b45" font-family="Arial,sans-serif">',
         '<text x="12" y="25" font-size="18">Known-English controls</text>',
         '<text x="12" y="48" font-size="13">Nearest profile is not always the true language</text>',
         '<text x="131" y="79" font-size="12">Letters</text><text x="209" y="79" font-size="12">GP labels</text><text x="285" y="79" font-size="12">Rune units</text>']
    for i,(label,row) in enumerate(zip(labels,report['sections'])):
        y=107+i*33
        out.append(f'<path d="M12 {y+12}H347" stroke="#d8dcd9"/><text x="12" y="{y}" font-size="13">{label}</text>')
        for j,mode in enumerate(modes):
            out.append(f'<text x="{131+j*78}" y="{y}" font-size="12">{row["comparisons"][mode][0]["language"]}</text>')
    out += ['<text x="12" y="455" font-size="13">Letters and GP labels use rune-derived text.</text>',
            '<text x="12" y="476" font-size="13">Rune units are compared with GP-grouped corpus.</text>',
            '<text x="12" y="500" font-size="13">Same eight candidate languages in every comparison.</text></g></svg>']
    return '\n'.join(out)+'\n'


if __name__=='__main__':
    report=calculate()
    for name,text in {'results.json':json.dumps(report,ensure_ascii=False,indent=2)+'\n','controls.svg':figure(report)}.items():
        if '--check' in sys.argv:assert (HERE/name).read_text(encoding='utf-8')==text,name
        else:(HERE/name).write_text(text,encoding='utf-8',newline='\n')
    print('PASS: known-reading results and control chart reproduce')
