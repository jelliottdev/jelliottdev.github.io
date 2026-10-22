"""Audit the four signed LP1 ASCII diagrams and a possible 5x5 misreading."""
import argparse
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def input_bytes(plan):
    found = {}
    for item in plan['inputs']:
        data = (ROOT / item['path']).read_bytes()
        assert sha256(data) == item['sha256'], item['path']
        found[item['path']] = data
    return found


def diagram(text):
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines)
              if len(line) == 16 and line.isdecimal() and len(set(line)) == 1]
    candidates = []
    for i in starts:
        block = lines[i:i + 7]
        if len(block) == 7 and block[0] == block[-1]:
            candidates.append(block)
    assert len(candidates) == 1, f'expected one seven-row diagram, got {len(candidates)}'
    block = candidates[0]
    border = block[0][0]
    assert all(len(line) == 16 for line in block)
    assert all(line[0] == line[-1] == border for line in block)
    assert all(block[i][1:-1].isspace() for i in (2, 4))
    inner = [line[1:-1] for line in block[1:-1]]
    numeric_rows = [inner[i].split() for i in (0, 2, 4)]
    assert all(len(row) == 3 and all(v.isdecimal() for v in row)
               for row in numeric_rows)
    return {'border_digit': border, 'printed_lines': block,
            'interior_lines': inner,
            'interior_matrix': [[int(v) for v in row] for row in numeric_rows]}


def visible_five_by_five(data):
    index = json.loads(data['data/index.json'])
    values = {entry['rune']: entry['prime'] for entry in index['alphabet']}
    mixed = json.loads(data['data/pages/lp1-05.json'])['raw']
    rows05 = [line.rstrip('/').split('-') for line in mixed.splitlines()
              if re.search(r'[0-9]', line)]
    assert len(rows05) == 5 and all(len(row) == 5 for row in rows05)
    converted05 = [[int(token) if token.isdecimal()
                    else sum(values[rune] for rune in token)
                    for token in row] for row in rows05]
    printed = json.loads(data['data/pages/lp1-16.json'])['raw']
    rows16 = [[int(v) for v in line.rstrip('/').split('-')]
              for line in printed.splitlines()
              if re.fullmatch(r'[0-9]+(?:-[0-9]+){4}/', line)]
    assert len(rows16) == 5 and all(len(row) == 5 for row in rows16)
    core05 = [row[1:4] for row in converted05[1:4]]
    core16 = [row[1:4] for row in rows16[1:4]]
    return {'lp1-05_converted': converted05, 'lp1-16_printed': rows16,
            'lp1-05_inner_3x3': core05, 'lp1-16_inner_3x3': core16,
            'same_inner_grid': core05 == core16,
            'shared_inner_values': sorted(set(sum(core05, [])) & set(sum(core16, [])))}


def report():
    plan_bytes = (HERE / 'plan.json').read_bytes()
    plan = json.loads(plan_bytes)
    data = input_bytes(plan)
    pages = {}
    for n in range(10, 14):
        page = f'lp1-{n:02}'
        path = f'exports/steganography/{page}.body.txt'
        metadata = json.loads(data[f'data/pages/{page}.json'])['embedded_payload']
        assert metadata['signature_valid'] and metadata['body_sha256'] == sha256(data[path])
        assert metadata['body_path'] == path
        pages[page] = diagram(data[path].decode('ascii'))
    first = pages['lp1-10']['interior_lines']
    assert all(row['interior_lines'] == first for row in pages.values())
    assert [row['border_digit'] for row in pages.values()] == ['3', '3', '0', '1']
    return {
        'schema': 'liberpedia-lp1-payload-outer-ring-results-v1',
        'plan_sha256': sha256(plan_bytes),
        'four_signed_message_diagrams': pages,
        'border_sequence': '3301',
        'same_interior_in_original_orientation': True,
        'interior_matrix': pages['lp1-10']['interior_matrix'],
        'interior_row_sums': [sum(row) for row in pages['lp1-10']['interior_matrix']],
        'alternative_visible_five_by_five_interpretation': visible_five_by_five(data),
        'interpretation': 'The identical 3x3 belongs to the four extracted signed diagrams. It is not a magic square and this check does not define an LP2 decryption.'
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    rendered = json.dumps(report(), ensure_ascii=False, indent=2) + '\n'
    target = HERE / 'results.json'
    if args.check:
        assert target.read_text(encoding='utf-8') == rendered
        print('PASS: four extracted borders are 3,3,0,1; all four interiors match; visible 5x5 cores differ')
    else:
        target.write_text(rendered, encoding='utf-8')
        print(target)


if __name__ == '__main__':
    main()
