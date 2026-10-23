"""Hash the reviewed files for the R24-C1-ext source-gate audit."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ID = 'dukotah-nonenglish-control-gate'
BASE = f'experiments/records/{ID}/'
SRC = ('plan.json', 'source-manifest.json', 'source-PREREG.md', 'source-control.py',
       'source-out_control.json', 'source-readjudicate.py', 'source-results.json',
       'LICENSE.source', 'check.py', 'plot.py', 'make_record.py', 'article.md')
OUT = ('results.json', 'control-gate.svg')


def entry(name):
    return {'path': BASE + name, 'sha256': hashlib.sha256((HERE / name).read_bytes()).hexdigest()}


record = {
    'id': ID,
    'status': 'draft',
    'title': 'A language-search control did not pass its frozen rule',
    'question': 'Did four archived non-English language controls satisfy the source’s preregistered power test?',
    'reader_question': 'Were proposed Latin, Greek, Old English and Enochian LP2 readings actually ruled out?',
    'summary': 'The source reports 20,480 decodes, but its four language controls all tie the English scorer on the frozen detection-rate test. The program substituted a different comparison to proceed.',
    'finding': 'All four own-language models and the English scorer cleared their respective wrong-key maxima on all 24 plants per language. None satisfies the frozen requirement that the own-language model have strictly greater detection power. The program instead compared d-prime scores and marked all four validated. Its reported zero manuscript survivors is not a control-validated exclusion under the original rule.',
    'limitations': 'This independently audits the pinned plan, source decision logic and saved summary rows; it does not rerun the 24-plant simulations, their 60 wrong-key decodes per language, or the reported 20,480 manuscript decodes. The outcome does not say whether any proposed language is the plaintext.',
    'next_steps': 'Freeze a control with measurable power to distinguish the languages, then rerun the same complete search and its matched null using one unchanged decision rule.',
    'outcome': 'inconclusive',
    'tags': ['language models', 'source audit', 'positive controls', 'selection effects', 'LP2'],
    'scope': {
        'pages': [],
        'artifacts': [BASE + 'source-PREREG.md', BASE + 'source-control.py', BASE + 'source-out_control.json'],
        'representation': 'Pinned Dukotah R24-C1-ext plan, Python decision code, and the saved 24-plant/60-wrong-key summary for four non-English registers. No manuscript run was performed locally.',
        'procedure': 'Verify Git-object hashes; independently evaluate the strict power inequality in the plan and the d-prime inequality in the program on each saved register row; compare the validated-register lists.',
        'parameters': 'Latin, Greek, Old English and Enochian; source control length 120 runes, 24 plants and 60 wrong-key controls per language. A source-reported 20,480-case LP2 grid is contextual, not locally rerun.',
        'exclusions': 'No conclusion about actual plaintext language, the entire key family, the source’s numeric manuscript scores, other source registers, or a control with different difficulty or thresholds.',
    },
    'review': {
        'kind': 'pinned-source control-rule audit',
        'retested_on': '2026-10-23',
        'reviewer': 'Independent saved-row and source-rule checker; original simulation and manuscript grid not rerun',
        'human_review': 'pending',
    },
    'reproduction': {
        'command': f'python {BASE}check.py && python {BASE}plot.py --check',
        'environment': 'Python 3 standard library; source files and saved receipts from pinned Git revision are bundled.',
        'script': BASE + 'check.py',
        'script_sha256': entry('check.py')['sha256'],
        'inputs': [entry(name) for name in SRC],
        'outputs': [entry(name) for name in OUT],
    },
    'visuals': [{'path': BASE + 'control-gate.svg', 'caption': 'For each non-English register, both scorers found all 24 plants; the preregistered rule required the own-language model to outperform English.'}],
    'sources': [
        {'label': 'Pinned R24-C1-ext frozen plan', 'url': 'https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round24/C1-ext-nonenglish/PREREG.md'},
        {'label': 'Pinned R24-C1-ext control program and saved results', 'url': 'https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round24/C1-ext-nonenglish/control.py'},
        {'label': 'Pinned R24-C1-ext reported manuscript result', 'url': 'https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round24/C1-ext-nonenglish/RESULTS.md'},
    ],
    'related': ['rune-matched-scorer-calibration', 'target-sized-languages'],
}
(HERE / 'record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print('Wrote', HERE / 'record.json')
