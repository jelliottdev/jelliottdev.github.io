"""Build the nine-source-ID batch receipt from exact pinned blobs and local runs."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[3].parent / 'source-cache' / 'dukotah-cicada3301'
REV = 'f08b20b632d91209ddbaa747e8e2f23df0c78ba1'
A = 'liber-primus/analysis/'
L6 = A + 'round18/L6-offset-marsaglia/'
C2 = A + 'round19/C2/'


def evidence(path):
    if path.startswith(A):
        raw = subprocess.check_output(['git', '-C', str(SOURCE), 'show', f'{REV}:{path}'])
    else:
        raw = (HERE / path).read_bytes()
        path = 'research/source-intake/batch20b-2026-10-23/worker-a/' + path
    return {'path': path, 'sha256': hashlib.sha256(raw).hexdigest()}


def entry(source_id, state, paths, executions, claim, remaining):
    return {'source_id': source_id, 'state': state,
            'evidence': [evidence(p) for p in paths], 'executions': executions,
            'covered_subclaim': claim, 'remaining': remaining}


builder = {'command': 'python -X utf8 -c "...run_path(pinned audit_builders.py) with X.OUT=worker-a"',
           'exit_code': 0, 'output_path': 'research/source-intake/batch20b-2026-10-23/worker-a/audit.json'}
control = {'command': 'python -X utf8 research/source-intake/batch20b-2026-10-23/worker-a/run_control_offset.py',
           'exit_code': 0, 'output_path': 'research/source-intake/batch20b-2026-10-23/worker-a/control_offset.json'}
saved = {'command': 'python -X utf8 research/source-intake/batch20b-2026-10-23/worker-a/audit_saved.py',
         'exit_code': 0, 'output_path': 'research/source-intake/batch20b-2026-10-23/worker-a/saved-check.json'}
pilot = {'command': 'python -X utf8 research/source-intake/batch20b-2026-10-23/worker-a/run_a1_pilot.py',
         'exit_code': 1, 'output_path': 'research/source-intake/batch20b-2026-10-23/worker-a/pilot-a1.json'}
fetch = {'command': 'python -X utf8 research/source-intake/batch20b-2026-10-23/worker-a/fetch_pinned_corpora.py',
         'exit_code': 1, 'output_path': 'research/source-intake/batch20b-2026-10-23/worker-a/corpora-receipt.json'}

entries = [
    entry('B-02', 'partial', [L6+'PREREG.md', L6+'scripts/audit_builders.py', L6+'scripts/control_offset.py',
          L6+'out/results_A1.json', L6+'out/results_A2.json', 'audit.json', 'control_offset.json',
          'input-reconstruction.json', 'pilot-a1.json', 'corpora-receipt.json', 'corpus-recovery-check.json'],
          [builder, control, pilot, fetch],
          'Fresh converter/sharding/beam audit passes. Reconstructed 12,956-rune ciphertext supports a 40/40 planted decoder control; top-1000 offset survival is 26/40. These are a KJV-only prefilter replay, not exact source-model parity. Source-saved A1 covers 220/220 units and A2 508/3024; arithmetic independently checked.',
          ['Pinned four-corpus trigram model cannot be rebuilt: exact Moby/Pride bytes absent; current Gutenberg hashes differ.',
           'A1 unit 0 replay on fallback model disagrees with pinned checkpoint score/rank; no source-exact target negative is reproduced. Matching aggregate control counts cannot validate which true offsets survive.',
           'A2 2516 source units and other generators/offsets remain unrun.']),
    entry('B-08', 'partial', [L6+'PREREG.md', L6+'out/results_A1.json', L6+'out/results_A2.json', 'saved-check.json'],
          [saved],
          'Source-saved A1/A2 finite offsets and seed/generator configurations are counted independently. Offset dimension is not the >2^32 seed dimension.',
          ['Seeds above 2^32, other generator families, and broad nonzero-offset combinations remain outside the finite source grids.',
           'Exact four-corpus source scorer unavailable locally.']),
    entry('B-13-MARSAGLIA', 'blocked', [L6+'PREREG.md', L6+'out/results_M.json', C2+'out_marsaglia_space.json'],
          [],
          'Pinned source reports a partial Marsaglia sweep; independent arithmetic confirms 17,639,963,712 planned pad-offset cases.',
          ['The 1.2 GB gitignored CDROM data are not in the pinned Git checkout; no fresh pad hash verification or sweep was run.',
           'Current English scorer corpus also fails exact hash gate.']),
    entry('R19-C2-PREFILTER-REGISTER', 'partial', [C2+'out_prefilter_register_power.json', C2+'out_prefilter_union.json',
          C2+'scripts/prefilter_register_power.py', 'saved-check.json'],
          [saved],
          'Independently recounted all 300 saved trial rows, per-register summaries, and four-screen unions; source-saved English top-1000 23-24/30, no-vowel 0/30.',
          ['This checks archived arithmetic only. Exact Marsaglia pad and exact four-corpus model are absent; source 300 planted scans were not rerun.']),
    entry('R19-C2-B02-ACCOUNTING', 'partial', [C2+'out_offset_coverage.json', C2+'scripts/offset_coverage.py',
          L6+'out/results_A1.json', L6+'out/results_A2.json', 'saved-check.json'],
          [saved],
          'Independently recomputed saved B-02 percentages and L6 A1/A2 unit × offset arithmetic; source reports 16 pre-L6 distinct key offsets against its chosen 2^20 bound.',
          ['The 2^20 denominator is a declared mechanism bound, not a natural limit on arbitrary generators.',
           'Full originating-lane raw rows/checkpoint collection and full C2 script execution were not independently reproduced.']),
    entry('R19-C2-MARSAGLIA-GATE', 'blocked', [C2+'out_verify.json', C2+'scripts/verify_marsaglia_independent.py',
          'corpora-receipt.json', 'corpus-recovery-check.json'], [fetch],
          'Saved source verification claims 112/112 input items passed; current exact-input check separately found two scorer corpus mismatches.',
          ['CDROM and extracted 10 MB pads are gitignored and absent locally, so the 112 file digests were not independently reverified.']),
    entry('R19-C2-MARSAGLIA-COST', 'partial', [C2+'out_marsaglia_space.json', C2+'scripts/marsaglia_space.py',
          'saved-check.json'], [saved],
          'Independently recomputed the 63-pad, six-builder, two-order, two-sign offset total (17,639,963,712) and ISO total from declared byte sizes.',
          ['The source wall-time estimate depends on missing original checkpoint mtimes and machine conditions; no new pad throughput benchmark was run.']),
    entry('B-02-C2-CORRECTION', 'duplicate', [L6+'ledger.json', C2+'out_offset_coverage.json',
          C2+'out_prefilter_register_power.json', 'saved-check.json'], [saved],
          'This is a status correction for B-02, not a new cipher test. The saved partial A2 coverage and measured prefilter loss support a scope-limited reading.',
          ['Only the source owner can amend its ledger; Liberpedia must not inherit a whole-axis negative from this source status.']),
    entry('R17-PUBLIC-PAD-C2-RESTATEMENT', 'duplicate', [C2+'out_prefilter_register_power.json',
          C2+'out_prefilter_union.json', 'saved-check.json'], [saved],
          'This is a coverage-line restatement, not a new pad search. Source-saved 300 plants show register-dependent prefilter survival, so its English survival factor is not universal.',
          ['No exact pad-level R17 negative was reproduced; non-English candidate coverage remains conditional.']),
]
assert len(entries) == 9 and len({e['source_id'] for e in entries}) == 9
receipt = {'schema': 'liberpedia-batch20b-worker-a-v1', 'source_revision': REV,
           'method_note': 'State describes independent work in this worker, not source author status. Missing gitignored files are not asserted unavailable everywhere.',
           'exact_model_gate': {'required':['kjv.txt','moby.txt','pride.txt','war.txt'],
                                'pinned_hashes_matched':['kjv.txt','war.txt'],
                                'pinned_hashes_failed_current_download':['moby.txt','pride.txt'],
                                'fallback_note':'The 40-trial control uses a KJV-only retrained trigram prefilter; it is not source-exact despite similar aggregate survival.'},
           'entries': entries}
(HERE / 'receipt.json').write_text(json.dumps(receipt, indent=2, ensure_ascii=False)+'\n', encoding='utf-8', newline='\n')
print('Wrote nine entries:', {s:sum(e['state']==s for e in entries) for s in ('replayed','partial','blocked','duplicate')})
