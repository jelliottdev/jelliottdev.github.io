"""Assemble metadata for the fixed-map sensitivity measurement."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
IDENT = HERE.name


def item(name):
    p = HERE / name
    return {'path': p.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}


plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
baseline = json.loads((ROOT / 'experiments/records/transcription-correction-sensitivity/record.json').read_text(encoding='utf-8'))
scope = {
    'pages': [f'lp2-{i:02d}' for i in range(58)],
    'representation': 'Every GP29 rune in the exact 13,136-rune source text, joined across punctuation and page boundaries; includes both solved closing pages.',
    'procedure': 'Enumerate all 27 uniform O/A/AE-to-O/A/AE mappings. Count equal neighbors and raw collision probability; report a fixed 29-symbol IoC multiplier separately from the source program’s observed-alphabet multiplier. Independently materialize every remapped stream.',
    'parameters': '3^3=27 deterministic maps; six bijections; three complete collapses; 13,135 adjacent pairs. No random control or language-score cutoff.',
    'exclusions': 'Individual glyph adjudication, context-dependent assignments, other rune families, word-boundary revisions, original image-clustering replay, decoder recovery and language identification.'}
record = {
    'id': IDENT, 'status': 'draft', 'title': 'What if O, A and AE were treated as one rune?',
    'question': 'How much do repeat counts and IoC change under every uniform remapping within the O/A/AE family, and are the source’s before-and-after scales identical?',
    'reader_question': 'Could confusing O, A and AE explain the repeat counts?',
    'summary': 'All 27 uniform assignments reproduce the source’s family-collapse arithmetic. Complete merging raises equal neighbors from 89 to 192 and fixed-scale IoC from 1.00 to 1.22; the source’s 1.14 uses a different multiplier after merging.',
    'finding': 'On 13,136 source runes, six bijections preserve 89 equal neighbors and normalized IoC 0.999842. The three complete collapses maximize both statistics among the 27 maps: 192 equal neighbors, raw IoC 0.0421113 and fixed29 IoC 1.221229. The unchanged source script instead reports 1.137006 because it changes its alphabet multiplier from 29 to 27.',
    'reader_finding': 'Merging all three rune types increases equal neighbors from 89 to 192. Merely swapping their names changes neither statistic. The source’s comparison also changes scale: keeping the same IoC multiplier gives 1.22 after merging, rather than 1.14.',
    'reader_limit': 'These are uniform label changes in a text sample that includes the solved closing pages. They do not decide any glyph reading or show how an unknown cipher would respond to errors.',
    'limitations': scope['exclusions'] + ' This finite bound applies only to the declared 27 uniform maps. Shape-clustering agreement cannot identify a global naming permutation, and ciphertext statistics do not bound an unknown decoder’s error sensitivity.',
    'next_steps': 'Adjudicate disputed shapes from images independently of canonical labels; carry explicit alternatives through a specified decoder before claiming that transcription errors can or cannot affect recovery.',
    'tags': ['O A AE', 'rune family', 'uniform remapping', 'transcription errors', 'IoC', 'normalization', 'equal neighbors', 'doublets', 'rune readings', 'O/A/AE ambiguity', 'O/A/AE rune readings'],
    'scope': scope, 'family': baseline['family'],
    'variant': {'label': 'All uniform assignments within one ambiguous rune family', 'changes': [
        {'field': k, 'before': baseline['scope'][k], 'after': v,
         'reason': 'A deterministic whole-family sensitivity check differs from stored individual transcription corrections.'}
        for k, v in scope.items() if baseline['scope'][k] != v]},
    'outcome': 'supported',
    'reproduction': {
        'command': f'python experiments/records/{IDENT}/run.py --check && python experiments/records/{IDENT}/check.py',
        'environment': 'Python 3.9 or later; standard library for the census, independent checker and plot. The separately saved original source exposure run uses NumPy.',
        'script': item('run.py')['path'], 'script_sha256': item('run.py')['sha256'],
        'inputs': [plan['input']] + [item(n) for n in ('plan.json', 'run.py', 'check.py', 'plot.py', 'package.py', 'article.md', 'source-crypto_exposure.py', 'source-FINDINGS.md', 'source-replay.json', 'LICENSE.source')],
        'outputs': [item('results.json'), item('collapse.svg')]},
    'review': {'reviewer': 'Independent full-stream census, permutation controls and unchanged source numerical exposure replay', 'retested_on': '2026-10-23', 'kind': 'computational', 'human_review': 'pending'},
    'sources': [{'label': 'Pinned source shape-audit findings', 'url': 'https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/independent-read/FINDINGS.md'},
                {'label': 'Original exposure calculation', 'url': 'https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/independent-read/crypto_exposure.py'}],
    'related': ['transcription-correction-sensitivity', 'rune-reading-sensitivity-t3', 'cross-source-word-boundaries'],
    'visuals': [{'path': item('collapse.svg')['path'], 'caption': 'Uniformly merging O, A and AE increases equality counts. Both IoC values shown use the same 29-symbol multiplier; this measures a transcription change, not a decipherment.'}]}
(HERE / 'record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
