"""Generate compact responsive clock diagrams from the frozen key conventions."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def diagram(title, note, rows, path):
    width = 480
    pieces = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 194" '
              'role="img" aria-labelledby="title description">',
              f'<title id="title">{title}</title><desc id="description">{note}</desc>',
              '<rect width="480" height="194" fill="#f5f7f8"/>',
              f'<text x="16" y="27" font-size="17" font-weight="700" fill="#26333a" '
              f'font-family="system-ui,sans-serif">{title}</text>',
              f'<text x="16" y="46" font-size="11" fill="#52616a" '
              f'font-family="system-ui,sans-serif">{note}</text>']
    for col in range(12):
        x = 84 + 31 * col
        pieces.append(f'<text x="{x+14}" y="70" text-anchor="middle" font-size="11" '
                      f'fill="#586770" font-family="system-ui,sans-serif">{col}</text>')
    for row_num, (label, values) in enumerate(rows):
        y = 80 + row_num * 45
        pieces.append(f'<text x="16" y="{y+22}" font-size="11" fill="#26333a" '
                      f'font-family="system-ui,sans-serif">{label}</text>')
        for col, value in enumerate(values):
            x = 84 + 31 * col
            pieces.append(f'<rect x="{x}" y="{y}" width="28" height="30" rx="2" '
                          'fill="#e5ebef" stroke="#cad3d9"/>')
            pieces.append(f'<text x="{x+14}" y="{y+21}" text-anchor="middle" '
                          'font-size="12" font-weight="600" fill="#24566d" '
                          f'font-family="system-ui,sans-serif">{value}</text>')
    pieces.append('<text x="16" y="183" font-size="10" fill="#52616a" '
                  'font-family="system-ui,sans-serif">Numbers are key slots or GP rune indices; j is the ciphertext-rune position.</text>')
    pieces.append('</svg>')
    path.write_text(''.join(pieces) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    diagram('Rotation changes after one key cycle', 'Archived key-01 has nine rune positions; phase zero shown.',
            [('Rotate left', list(range(9)) + [1, 2, 3]),
             ('Fold ends', list(range(9)) + [8, 7, 6])],
            ROOT / 'experiments/records/rotating-folded-key-openings/clock.svg')
    diagram('Keyword changes the alphabet', 'Key-01, first twelve positions of the mixed GP29 alphabet.',
            [('GP order', list(range(12))),
             ('Mixed', [24, 23, 8, 18, 4, 9, 5, 0, 1, 2, 3, 6])],
            ROOT / 'experiments/records/mixed-alphabet-key-openings/clock.svg')
    diagram('One key rune can cover a group', 'Group size three; two fixed boundary offsets.',
            [('Offset 0', [j // 3 for j in range(12)]),
             ('Offset 1', [(j + 1) // 3 for j in range(12)])],
            ROOT / 'experiments/records/grouped-key-advance-openings/clock.svg')
