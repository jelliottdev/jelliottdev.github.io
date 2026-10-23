"""Build an internal, source-pinned triage of all archived Wulfic legacy scripts.

This classifies source, not outcomes. No manuscript experiment runs here.
"""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
UPSTREAM = Path('C:/Users/ianex/Documents/Codex/2026-10-19/i-w/work/source-archives/Wulfic-Cicada3301-Liber_Primus')
COMMIT = 'bf89d3d13aad2b8f2c95ab195cf1b092f250775c'
PREFIX = 'tools/legacy/'

# Every filename appears exactly once. Grouping is by the tested operation, not
# by the number of launchers, postprocessors, or optimizer versions.
GROUPS = {
    'archive-maintenance': '''add_circumference_anchor populate_runes translate_runes''',
    'external-clue-inspection': '''analyze_hints verify_circumference''',
    'page-statistics-and-diagnostics': '''cipher_analysis deep_page_analysis structural_analysis p08_grid_analysis p20_count p02_analyze p24_char_tests p24_prime0_post''',
    'first-pass-cipher-sweeps': '''advanced_cipher_solver batch_solver session16_deep_solve session17_clean_solve theory_orchestrator solve_p21_30''',
    'monoalphabetic-substitution': '''mono_sub_solver hillclimb_substitute p21_refined_subsweep''',
    'adfgvx-fractionation': '''adfgvx_test''',
    'keyword-prime-double-layer': '''combined_cipher_test keyword_stepped_stream prime_stream_solver p21_30_keyword_sweep verify_keyword_ioc''',
    'autokey-feedback': '''autokey_comprehensive p21_30_autokey_solver stream_cipher_attack''',
    'running-key-corpora': '''gpu_running_key test_lp1_runningkey''',
    'periodic-crib-constraints': '''period_crib_solve lp_crib_drag beaufort_crib crib_verify validate_crib_candidates check_p32_crib''',
    'two-time-pad-cribs': '''twotime_pad_analysis twotime_crib ttp_crib_drag''',
    'lfsr-and-formula-keys': '''lfsr_gf29_solver lfsr_singleton_solver lfsr4_solver lfsr4_fast lfsr_alberti_solver singleton_stream_search''',
    'transposition-rearrangement': '''transposition_solver p21_30_rearrange p21_30_transposition p21_30_verified_rearrange refine_and_batch''',
    'deor-interlocking': '''p20_interlocking solve_p20''',
    'targeted-solved-reading-keys': '''decode_p14_p15 solve_p61_p62 fskip_verified_solver verify_key_parse''',
    'targeted-page02-cribs': '''p02_crib_drag p02_crib_extend p02_crib_refine p02_hillclimb2 p02_known_plaintext p02_p18_deepsolve p02_sa_solve''',
    'targeted-page24-optimizers': '''p24_apply_targeted_map p24_candidate_process p24_process_top_candidates p24_refine p24_seeded_hillclimb p24_view_candidate''',
    'targeted-page25-optimizers': '''p25_hillclimb p25_liberal_offset_sweep''',
    'anchored-hillclimbers': '''anchored_hillclimb_modes_p21 anchored_hillclimb_p21 anchored_hillclimb_pages21_30 crib_extension extract_confirmed_cribs find_new_cribs update_anchors rank_anchored_results segment_anchored_results export_top_candidates''',
    'gpu-key-optimization': '''gpu_hillclimber gpu_hillclimber_v2 gpu_hillclimber_v3 gpu_hillclimber_v4 hillclimb_monitor monitor_gpu_output analyze_v3_decode decode_best_key check_cuda_ascii''',
    'key-postprocessing-and-verification': '''analyze_verified_keys decrypt_page_with_verified_key extract_lp_text gap_filler generate_runeglish key_pattern_analysis refine_verified_keys segment_runeglish show_current_decode verify_decode word_refine diagnose_free_text''',
    'targeted-page21-and-p43': '''p21_30_second_layer solve_p43_p00''',
}

META = {
    'archive-maintenance': ('utility', 'Corpus preparation only; not a cipher attempt. Audit changes to source files before any reuse.', []),
    'external-clue-inspection': ('partial', 'Pin the hint or circumference source artifact and check whether an actual finite decryption rule is stated.', []),
    'page-statistics-and-diagnostics': ('partial', 'Crosswalk each statistic or assertion against published measurements, then isolate any untested predictor with a predeclared control. Page-name corrections are required.', ['wulfic-letter-encoding-bounds']),
    'first-pass-cipher-sweeps': ('open_optimizer', 'Extract finite operator definitions and a common score/selection gate; do not count parameterized sweeps as independent failures.', []),
    'monoalphabetic-substitution': ('partial', 'Separate complete whole-page substitution from short seeded hillclimbs; compare with existing crib-capacity and direct-affine records before a new controlled run.', ['monoalphabetic-crib-capacity']),
    'adfgvx-fractionation': ('replayed_adaptation', 'Already tested as a corrected-input bounded adaptation; source shortcuts and other fractionation layouts remain outside scope.', ['wulfic-adfgvx-fractionation']),
    'keyword-prime-double-layer': ('partial', 'The combined layer and three additional finite prime/keyword script grids have bounded replays. verify_keyword_ioc.py and any untested screen or key interpretation remain open.', ['wulfic-keyword-prime-layer-grid', 'wulfic-prime-keyword-stream-families']),
    'autokey-feedback': ('partial', 'Compare exact feedback clock, reset and skip rules against cumulative and ciphertext-autokey records; freeze original target mapping and full selection.', ['cumulative-autokey-literal', 'multiplicative-ciphertext-autokey']),
    'running-key-corpora': ('partial', 'Source LP1 key selection mixes solved and unsolved pages under old numbering. Correct source/input mapping before any original claim; genuine solved-reading and named-corpus keys have narrower existing tests.', ['solved-reading-running-key', 'emerson-running-key']),
    'periodic-crib-constraints': ('partial', 'period_crib_solve.py has a source-output replay and a separately declared held-out diagnostic whose planted-recovery gate failed. Checkpoint-dependent validators and the distinct lp_crib_drag.py model remain unexecuted.', ['wulfic-periodic-word-crib-votes', 'periodic-affine-crib-capacity']),
    'two-time-pad-cribs': ('partial', 'The three scripts’ claimed aligned-copy premises and one all-page-pair frequency screen are replayed. Their downstream crib placements were not scored after the named alignments failed; other shared-key models remain open.', ['wulfic-two-time-pad-premise', 'leo-shared-key-differences']),
    'lfsr-and-formula-keys': ('partial', 'GF29 singleton LFSR finite grid has a separate draft. Fast/ordinary LFSR4 are optimizer aliases; Alberti and formula branches need rule-by-rule crosswalk and input correction.', ['wulfic-lfsr-singleton-constraints']),
    'transposition-rearrangement': ('partial', 'transposition_solver.py has a source-exact fixed-key route replay on its actual LP2-04–13 inputs. Its four sibling scripts use different word/optimizer gates or absent source inputs; their additional branches remain open.', ['wulfic-keyed-transposition-cohort', 'lp2-row-column-routes']),
    'deor-interlocking': ('partial', 'Exact P20 source gate and corrected normalized diagnostic are drafted. solve_p20 targets a different older count/input: verify its actual stream and key rule before treating it as the same test.', ['wulfic-deor-interlocking-streams']),
    'targeted-solved-reading-keys': ('blocked_input', 'Verify original claimed known-reading plaintext, key provenance and page identity. Historical “solved” labels cannot serve as ground truth without independent source checks.', ['solved-reading-running-key']),
    'targeted-page02-cribs': ('open_optimizer', 'Group related crib, annealing and refinement versions; pin each actual source page and every assumed plaintext anchor before a bounded test.', []),
    'targeted-page24-optimizers': ('open_optimizer', 'Candidate viewing/refinement scripts are downstream of selected anchors; recover candidate provenance and exact target bytes before evaluation.', []),
    'targeted-page25-optimizers': ('open_optimizer', 'Check the source page mapping and candidate checkpoint, then derive a finite grid and planted recovery control if available.', []),
    'anchored-hillclimbers': ('open_optimizer', 'Treat anchor creation, optimization, rank/segment/export utilities as one dependency chain; independently verify anchors before scoring any candidate.', []),
    'gpu-key-optimization': ('open_optimizer', 'Four optimizer revisions plus monitor/view utilities share a mutable checkpoint lineage; pin checkpoint, training corpus, score and exact stopping gate.', []),
    'key-postprocessing-and-verification': ('blocked_input', 'These scripts consume selected keys/cribs and segment outputs. Pin upstream candidate and inspect whether verification is independent of the construction that selected it.', []),
    'targeted-page21-and-p43': ('partial', 'Correct old page labels and recover seed keys before source-specific second-layer or cross-page claims; do not adopt named high-IoC claims as independent discoveries.', []),
}

ITEM_OVERRIDES = {
    'combined_cipher_test.py': ('replayed_adaptation', ['wulfic-keyword-prime-layer-grid'],
                                'Complete corrected-input 224,128-cell source grid is recorded; do not count the sibling scripts as covered.'),
    'p20_interlocking.py': ('replayed_source_and_amended_diagnostic', ['wulfic-deor-interlocking-streams'],
                            'Exact source stdout reproduced. Its >1.3 and >1.5 raw-IoC gates are impossible; separate normalized control is recorded. This says nothing about solve_p20.py.'),
    'lfsr_gf29_solver.py': ('replayed_adaptation', ['wulfic-lfsr-singleton-constraints'],
                           'Complete source singleton-constraint grid is recorded on verified page identities; other formula branches in this script are not all replayed.'),
    'p21_30_keyword_sweep.py': ('replayed_source_bounded', ['wulfic-prime-keyword-stream-families'],
                                'Source repeating-keyword grid replayed on corrected page identities; this is an opening/singleton screen, not a verified decryption.'),
    'prime_stream_solver.py': ('replayed_source_bounded', ['wulfic-prime-keyword-stream-families'],
                               'Source prime generators, F-skip and screen replayed; permissive hits are not plaintext readings.'),
    'keyword_stepped_stream.py': ('replayed_source_bounded', ['wulfic-prime-keyword-stream-families'],
                                  'Source keyword-stepped stream and finite offset screen replayed; other arithmetic streams are outside scope.'),
    'period_crib_solve.py': ('replayed_source_with_control_limit', ['wulfic-periodic-word-crib-votes'],
                             'Two archived example page/period source outputs reproduced; held-out exact-word check found zero, but planted controls failed the predeclared recovery gate.'),
    'twotime_crib.py': ('replayed_source_premise_only', ['wulfic-two-time-pad-premise'],
                        'Named identical-ciphertext spans checked against the exact source stream; downstream shared-key crib placements were not scored.'),
    'twotime_pad_analysis.py': ('replayed_source_screen_and_premise', ['wulfic-two-time-pad-premise'],
                                'Named period/alignment premise and all 1,122 page-pair operation scores replayed; other running-key branches remain outside this record.'),
    'ttp_crib_drag.py': ('replayed_source_premise_only', ['wulfic-two-time-pad-premise'],
                         'Claimed P27/P44 prefix checked on corrected source pages; downstream crib dragging was not scored after the prefix failed.'),
    'transposition_solver.py': ('replayed_source_bounded', ['wulfic-keyed-transposition-cohort'],
                                'Entire source solve_page loop replayed on ten byte-aligned streams, with 80 planted route controls. Source best-score rows are not readings; four sibling scripts remain separate.'),
}


def main():
    files = sorted((UPSTREAM / PREFIX).glob('*.py'))
    assert len(files) == 107
    assignment = {}
    for group, words in GROUPS.items():
        for stem in words.split():
            name = stem + '.py'
            assert name not in assignment, name
            assignment[name] = group
    names = {path.name for path in files}
    assert names == set(assignment), {'missing': sorted(names - set(assignment)), 'extra': sorted(set(assignment) - names)}
    blobs = {}
    listing = subprocess.check_output(['git', 'ls-tree', '-r', COMMIT, '--', PREFIX], cwd=UPSTREAM, text=True)
    for line in listing.splitlines():
        metadata, path = line.split('\t', 1)
        blobs[path] = metadata.split()[2]
    entries = []
    for path in files:
        rel = PREFIX + path.name
        raw = path.read_bytes()
        actual_blob = hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()
        assert actual_blob == blobs[rel], f'local file differs from pinned commit: {rel}'
        source = raw.decode('utf-8-sig')
        tree = ast.parse(source, filename=rel)
        desc = ((ast.get_docstring(tree) or '').splitlines() or [''])[0]
        group = assignment[path.name]
        state, action, overlaps = META[group]
        if path.name in ITEM_OVERRIDES:
            state, overlaps, action = ITEM_OVERRIDES[path.name]
        found_pages = sorted({int(m.group(1)) for m in re.finditer(r'page_(\d{1,2})', source)})
        refs = sorted({value for node in ast.walk(tree) if isinstance(node, ast.Constant)
                       if isinstance(value := node.value, str)
                       if len(value) < 180 and re.search(r'\.(?:json|txt|tsv|csv|bin|npy|pkl|jpg|png)(?:$|\b)', value, re.I)})
        entries.append({
            'path': rel,
            'git_blob': blobs[rel],
            'source_url': f'https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/{COMMIT}/{rel}',
            'source_docstring_first_line': desc,
            'group_id': group,
            'triage': state,
            'literal_page_paths': found_pages,
            'literal_data_references': refs[:24],
            'related_site_records': overlaps,
            'remaining_work': action,
        })
    groups = []
    for group in GROUPS:
        state, action, overlaps = META[group]
        members = [entry['path'] for entry in entries if entry['group_id'] == group]
        groups.append({'id': group, 'script_count': len(members), 'triage': state,
                       'scope': action, 'related_site_records': overlaps, 'scripts': members})
    data = {
        'schema': 'liberpedia-wulfic-legacy-method-groups-v1',
        'date': '2026-10-23',
        'status': 'internal static source triage; no source result was certified by this inventory',
        'repository': 'https://github.com/Wulfic/Cicada3301-Liber_Primus',
        'commit': COMMIT,
        'source_warning': 'The upstream legacy README says old page/rune pairs and paths may be wrong. Current archived page_N maps 00..16 to LP1-00..16 and 17..74 to LP2-00..57; historic outputs need individual replay.',
        'counting_rule': '107 launchers/helpers are grouped into method/dependency families. Groups are queue units, not 22 independent cipher hypotheses or completed experiments.',
        'script_count': len(entries),
        'group_count': len(groups),
        'triage_counts_by_script': dict(Counter(entry['triage'] for entry in entries)),
        'priority_groups': ['autokey-feedback', 'transposition-rearrangement', 'periodic-crib-constraints', 'two-time-pad-cribs', 'keyword-prime-double-layer'],
        'groups': groups,
        'scripts': entries,
    }
    output = HERE / 'wulfic-legacy-method-groups-2026-10-23.json'
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f'{len(entries)} scripts in {len(groups)} groups -> {output.name}')


if __name__ == '__main__':
    main()
