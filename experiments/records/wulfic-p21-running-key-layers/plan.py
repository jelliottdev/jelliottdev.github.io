"""Freeze the source-defined P21–30 running-key grid before target scoring."""
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
HERE = pathlib.Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'source-archives' / 'Wulfic-Cicada3301-Liber_Primus'
REV = 'bf89d3d13aad2b8f2c95ab195cf1b092f250775c'
SOURCE_FILES = [
    'tools/legacy/p21_30_autokey_solver.py',
    'data/corpora/deor_poem.txt',
    'data/corpora/self_reliance.txt',
    'data/corpora/wordlist.txt',
]
SOURCE_FILES += [f'pages/page_{p:02d}/runes.txt' for p in range(21, 31)]

def blob(rel):
    return subprocess.check_output(['git', '-C', str(SOURCE), 'show', f'{REV}:{rel}'])

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    actual = subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD']).decode().strip()
    assert actual == REV, actual
    files = {name: {'sha256': sha(blob(name)), 'bytes': len(blob(name))} for name in SOURCE_FILES}
    site = {f'lp2-{p-17:02d}': sha((ROOT / f'data/pages/lp2-{p-17:02d}.json').read_bytes()) for p in range(21, 31)}
    plan = {
        'schema': 'liberpedia-wulfic-p21-running-key-plan-v1',
        'timing': 'retrospective source replay; source script was read before freezing this grid',
        'source_revision': REV,
        'source_url': 'https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/' + REV + '/tools/legacy/p21_30_autokey_solver.py',
        'source_files': files,
        'site_pages': site,
        'page_mapping': 'source global P21–30 = LP2-04–13, confirmed rune-for-rune',
        'key_sources': ['deor_poem', 'self_reliance'],
        'branches': {
            'running_key': {'offsets': 'range(0, len(key)-len(page), max(1,(len(key)-len(page))//200))', 'modes': ['sub', 'add', 'beaufort']},
            'keyword_plus_running_key': {'offsets': 'range(0, len(key)-len(page), max(1,(len(key)-len(page))//100))', 'keyword': 'single assigned PAGE_CONFIG vector', 'key_combine': ['keyword_plus_running', 'keyword_minus_running'], 'decode_modes': ['sub', 'add', 'beaufort']},
        },
        'source_gate': 'normalized 29× raw index of coincidence strictly >1.3; only passing outputs scored by source wordlist method',
        'selection': 'source per-page score then IoC ordering; retain all cases and report global top; no inferred reading from an isolated word hit',
        'controls': 'Before target, constructed full-length plaintext at LP2-04 source word lengths, encrypted by each mode and combination using declared DEOR offset 0; require complete recovery, IoC gate pass and positive source word score. Exact source-function parity on sampled cells.',
        'null': '49 seeded within-page rune shuffles, same shuffled page used for every candidate in that trial; repeat full grid and retain global maximum source score, seed 20261023. Descriptive retrospective selection control.',
        'limits': 'This tests only source corpus encodings, coarse offsets, source page/keyword assignments, normalization, score and exact word skeleton. No claim about other key text, offsets, languages or manuscript mechanism.',
    }
    HERE.joinpath('plan.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False) + '\n', encoding='utf8', newline='\n')
    print('plan_sha256', sha(HERE.joinpath('plan.json').read_bytes()))

if __name__ == '__main__':
    main()
