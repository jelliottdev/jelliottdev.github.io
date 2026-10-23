"""Declare the bounded Deor source replay and its reproducible files."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = f'experiments/records/{HERE.name}/'


def hashed(path):
    return {'path': path, 'sha256': hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main():
    result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    assert result['deor_gp_values'] == 960
    assert result['observed']['original_second_hits'] == 0
    assert result['null_second_ge_observed'] == 110
    assert result['null_first_ge_observed'] == 18
    files = [BASE + name for name in (
        'plan.json', 'plan-initial-frozen.json', 'input-parser-amendment.json',
        'deor-poem-source.txt', 'source-run.txt', 'run.py', 'replay_source.py',
        'check.py', 'plot.py', 'make_record.py', 'article.md')]
    files += ['data/index.json', 'text/lp2-03.txt']
    record = {
        'id': HERE.name,
        'status': 'draft',
        'title': 'Deor and interlocking rune streams',
        'question': 'Does the archived prime-index split and Deor-to-derived-key sequence produce a distinctive second-stream IoC on current LP2-03?',
        'reader_question': 'Can Deor unlock one stream and use it to unlock the rest?',
        'summary': 'The original source hit thresholds are impossible for its raw score. A separately normalized whole-procedure control finds no distinctive final-stage peak in this bounded test.',
        'finding': 'The unchanged source emits no HIT because its raw IoC is bounded by 1 while the HIT gates demand >1.3 and >1.5. On current LP2-03, it selects Deor add at offset47 (first raw IoC0.0649) and then subtract at repeat offset31 (second raw IoC0.0404). Under a separate 29×normalized diagnostic, the second maximum is1.173; 110 of199 whole-procedure shuffles reach at least that score. The first maximum is1.882; 18 of199 shuffles reach it.',
        'limitations': 'Zero original source HIT rows are not negative evidence because the gates cannot pass. The normalized test was frozen separately and measures only one page, one pinned Deor stream, a prime-index partition, the source direction/offset grids and one histogram-preserving shuffle model. Synthetic controls verify arithmetic, not power to detect English. Other two-stream ciphers remain untested.',
        'next_steps': 'A stronger proposal should specify how the streams are separated, how the first output keys the second, and a full expected reading or held-out prediction before inspecting the result.',
        'outcome': 'inconclusive',
        'tags': ['LP2', 'source replay', 'Deor', 'interlocking streams', 'index of coincidence', 'impossible source gate'],
        'scope': {
            'pages': ['lp2-03'],
            'artifacts': [BASE + 'source-run.txt', BASE + 'input-parser-amendment.json'],
            'representation': 'Current LP2-03 canonical GP29 rune values, exactly matching archived old page_20 after filtering; split by whether rune index is prime.',
            'procedure': 'Replay original code in a temp folder; independently run all 1,800 first-stage Deor variants, select maximum raw IoC, then all 195 repeating-derived-key variants, retaining original unreachable HIT gates. Separately compare 29×normalized maxima with 199 whole-procedure page shuffles.',
            'parameters': '217 runes:65 prime-index,152 other; source Old English Deor parser yields960 values; 3 modes×600 offsets and3 modes×65 repeat offsets; 29 Caesar shifts; 199 seeded page shuffles, seed20261023.',
            'exclusions': 'Other pages, alternative prime definitions/partitions, modern Deor translation, other poems, word resets, variable key feedback, other language scores and all untested stream rules.'
        },
        'review': {
            'kind': 'exact archived-source replay plus separately declared normalized diagnostic',
            'retested_on': '2026-10-23',
            'reviewer': 'Unchanged source stdout matches archived input; independent selected-decode arithmetic and full 199-control rerun; parser amendment retains initial failed exploratory result.',
            'human_review': 'pending'
        },
        'reproduction': {
            'command': f'python {BASE}check.py && python {BASE}plot.py --check',
            'environment': 'Python3 standard library. Exact original-script replay additionally requires a local checkout of pinned upstream revision bf89d3d13aad2b8f2c95ab195cf1b092f250775c.',
            'script': BASE + 'check.py',
            'script_sha256': hashed(BASE + 'check.py')['sha256'],
            'inputs': [hashed(path) for path in files],
            'outputs': [hashed(BASE + name) for name in ('results.json', 'comparison.svg')]
        },
        'visuals': [{'path': BASE + 'comparison.svg', 'caption': 'The original raw-score thresholds cannot be reached; a separate normalized full-search comparison finds no unusual final-stage peak.'}],
        'sources': [
            {'label': 'Pinned archived Deor two-stream script', 'url': 'https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/p20_interlocking.py'},
            {'label': 'Pinned Deor poem input', 'url': 'https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/data/corpora/deor_poem.txt'},
        ],
        'related': ['wulfic-keyword-prime-layer-grid', 'wulfic-letter-encoding-bounds']
    }
    (HERE / 'record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
