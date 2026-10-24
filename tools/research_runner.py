"""Run bounded rune transformations locally. No code execution or network access.

Usage: python tools/research_runner.py --task task.json --out results.json
Only rune characters move/change; separators retain their exact positions.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

TASK_SCHEMA = 'liberpedia-local-task-v1'
RESULT_SCHEMA = 'liberpedia-local-result-v1'
ENGINE = 'rune-program-v1'
MAX_FILE_BYTES = 2_000_000


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(value, expected, label):
    require(isinstance(value, dict) and set(value) == set(expected),
            label + ' has invalid fields')


def integer(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def task_identity(task):
    return hashlib.sha256(canonical({k: v for k, v in task.items() if k != 'taskId'})).hexdigest()


def validate(task):
    fields(task, ('schema', 'engine', 'taskId', 'title', 'pages', 'alphabet', 'steps', 'criterion'), 'Task')
    require(task['schema'] == TASK_SCHEMA and task['engine'] == ENGINE, 'Unsupported schema or engine')
    require(isinstance(task['taskId'], str) and re.fullmatch('[0-9a-f]{64}', task['taskId']), 'Invalid taskId')
    require(isinstance(task['title'], str) and task['title'].strip() and len(task['title']) <= 300, 'Invalid title')
    alphabet = task['alphabet']
    require(isinstance(alphabet, list) and len(alphabet) == 29, 'Alphabet must contain exactly 29 entries')
    runes = set()
    for entry in alphabet:
        fields(entry, ('rune', 'latin', 'prime'), 'Alphabet entry')
        rune = entry['rune']
        require(isinstance(rune, str) and len(rune) == 1 and not rune.isspace()
                and not 0xD800 <= ord(rune) <= 0xDFFF and rune not in runes, 'Invalid or duplicate rune')
        require(isinstance(entry['latin'], str) and 1 <= len(entry['latin']) <= 8, 'Invalid Latin label')
        require(integer(entry['prime'], 2, 1000000), 'Invalid prime value')
        runes.add(rune)
    pages = task['pages']
    require(isinstance(pages, list) and 1 <= len(pages) <= 75, 'Task needs 1–75 pages')
    seen, count, total_text = set(), 0, 0
    for page in pages:
        fields(page, ('id', 'text'), 'Page')
        identifier = page['id']
        require(isinstance(identifier, str) and re.fullmatch(r'lp[12]-[0-9]{2}', identifier)
                and identifier not in seen, 'Invalid or duplicate page ID')
        require(int(identifier[4:]) <= (16 if identifier[2] == '1' else 57), 'Page ID outside manuscript bounds')
        seen.add(identifier)
        require(isinstance(page['text'], str), 'Page text must be a string')
        total_text += len(page['text'])
        count += sum(ch in runes for ch in page['text'])
    require(count <= 20000, 'Task exceeds 20000 runes')
    require(total_text <= 300000, 'Task exceeds 300000 text codepoints')
    steps = task['steps']
    require(isinstance(steps, list) and len(steps) <= 8, 'Task exceeds 8 steps')
    for step in steps:
        require(isinstance(step, dict), 'Step must be an object')
        if step.get('op') == 'reverse':
            fields(step, ('op', 'unit'), 'Reverse step')
            require(step['unit'] in ('line', 'word', 'page'), 'Invalid reverse unit')
        elif step.get('op') == 'affine':
            fields(step, ('op', 'a', 'b'), 'Affine step')
            require(integer(step['a'], 0, 28) and integer(step['b'], 0, 28), 'Invalid affine coefficients')
        elif step.get('op') == 'cumulative-difference':
            fields(step, ('op', 'reset'), 'Cumulative step')
            require(step['reset'] in ('page', 'line', 'word'), 'Invalid cumulative reset')
        else:
            raise ValueError('Unsupported operation')
    criterion = task['criterion']
    require(isinstance(criterion, dict), 'Criterion must be an object')
    if criterion.get('kind') == 'exact-prefix':
        fields(criterion, ('kind', 'values'), 'Prefix criterion')
        require(isinstance(criterion['values'], list) and 1 <= len(criterion['values']) <= 256
                and all(integer(v, 0, 28) for v in criterion['values']), 'Invalid prefix values')
    else:
        fields(criterion, ('kind',), 'Measurement criterion')
        require(criterion['kind'] == 'measurement', 'Unsupported criterion')
    require(task['taskId'] == task_identity(task), 'Task identity does not match its contents')
    require(len(canonical(task)) <= MAX_FILE_BYTES, 'Task exceeds byte limit')
    return task


def boundary(character, unit, indices):
    return (unit == 'word' and character not in indices) or (unit == 'line' and character in '\r\n')


def transform(text, step, runes, indices):
    chars = list(text)
    if step['op'] == 'reverse':
        positions = []

        def flush():
            values = [chars[i] for i in positions][::-1]
            for i, value in zip(positions, values):
                chars[i] = value
            positions.clear()

        for i, ch in enumerate(chars):
            if boundary(ch, step['unit'], indices):
                flush()
            elif ch in indices:
                positions.append(i)
        flush()
    else:
        total = 0
        for i, ch in enumerate(chars):
            if ch in indices:
                if step['op'] == 'affine':
                    value = (step['a'] * indices[ch] + step['b']) % 29
                else:
                    value = (indices[ch] - total) % 29
                    total = (total + value) % 29
                chars[i] = runes[value]
            elif step['op'] == 'cumulative-difference' and boundary(ch, step['reset'], indices):
                total = 0
    return ''.join(chars)


def run(task):
    validate(task)
    runes = [entry['rune'] for entry in task['alphabet']]
    indices = {rune: i for i, rune in enumerate(runes)}
    transformed, matches, counts = [], [], Counter()
    pairs = equal = total = 0
    for page in task['pages']:
        text = page['text']
        for step in task['steps']:
            text = transform(text, step, runes, indices)
        values = [indices[ch] for ch in text if ch in indices]
        counts.update(values)
        total += len(values)
        pairs += max(0, len(values) - 1)
        equal += sum(a == b for a, b in zip(values, values[1:]))
        transformed.append({'page': page['id'], 'text': text})
        if task['criterion']['kind'] == 'exact-prefix':
            prefix = task['criterion']['values']
            matches.append({'page': page['id'], 'matched': values[:len(prefix)] == prefix})
    return {'schema': RESULT_SCHEMA, 'taskId': task['taskId'], 'engine': ENGINE,
            'metrics': {'pages': len(task['pages']), 'runes': total, 'adjacentPairs': pairs,
                        'equalAdjacentPairs': equal,
                        'ioc': sum(n * (n - 1) for n in counts.values()) / (total * (total - 1)) if total > 1 else 0.0},
            'matches': matches, 'transformed': transformed, 'runnerVersion': '1'}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON field: ' + key)
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        task_path, output = args.task.resolve(), args.out.resolve()
        require(output not in (task_path, Path(__file__).resolve()), 'Output cannot overwrite task or runner')
        require(not args.out.exists() and not args.out.is_symlink(), 'Output already exists')
        with task_path.open('rb') as handle:
            raw = handle.read(MAX_FILE_BYTES + 1)
        require(len(raw) <= MAX_FILE_BYTES, 'Task exceeds byte limit')
        task = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Invalid JSON constant')))
        result = run(task)
        payload = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n'
        # Exclusive creation also protects against a concurrent file appearing.
        with output.open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(payload)
    except (OSError, ValueError, TypeError, RecursionError) as error:
        parser.exit(2, 'research_runner: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
