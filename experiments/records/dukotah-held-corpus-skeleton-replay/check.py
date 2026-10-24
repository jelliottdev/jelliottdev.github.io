"""Check saved C-01 evidence and bundle bytes; no target or control simulation."""
import argparse,hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
def read(name):return json.loads((H/name).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def expected_results():
    manifest=read('reproduction/inputs-frozen.json');audit=read('reproduction/independent-target-audit.json');source=read('reproduction/scan_results.json')
    eligible=[x for x in manifest['corpus'] if x['words']>=2928]
    assert len(manifest['corpus'])==94 and sum(x['words'] for x in manifest['corpus'])==9808699
    assert len(eligible)==84 and sum(x['words'] for x in eligible)==9799472
    assert len(audit['omitted_short_texts'])==10
    assert audit['output_sha256']==sha(H/'reproduction/scan_results.json')
    assert audit['target_plan_sha256']==sha(H/'reproduction/target-plan-frozen.json')
    assert len(audit['global_witnesses'])==21
    names={x['name'] for x in eligible}
    for values in source['per_text'].values():
        assert set(values)==names and all(abs(v-round(v))<.01 for v in values.values())
    real=[]
    for witness in audit['global_witnesses']:
        saved=source['best'][witness['pattern']]
        assert abs(saved['count']-witness['count'])<.01
        assert (saved['text'],saved['offset'])==(witness['text'],witness['offset'])
        assert witness['unique_eligible_alignments']==sum(x['words']-witness['window']+1 for x in eligible)
        if witness['pattern'].startswith('real'):
            nulls=[x['count'] for x in audit['global_witnesses'] if x['pattern'].startswith('n') and x['window']==witness['window'] and x['pattern'].split(':')[1]==witness['pattern'].split(':')[1]]
            real.append(dict(pattern=witness['pattern'],window=witness['window'],count=witness['count'],text=witness['text'],offset=witness['offset'],shuffled_maxima=nulls))
    assert all(x['count']<x['window'] for x in real)
    return dict(source_id='C-01',source_revision=manifest['revision'],source_target_plan_sha256=sha(H/'reproduction/target-plan-frozen.json'),source_results_sha256=sha(H/'reproduction/scan_results.json'),held_texts=94,held_words=9808699,eligible_texts=84,eligible_words=9799472,omitted_short_texts=10,manuscript_words=2928,real_patterns=real,complete_real_pattern_matches=0,interpretation='Compatible word-length positions, not decoded words or calibrated global probabilities.',checks='Saved evidence/hash/arithmetic validation only; the original private replay and integer witness recounts are preserved, not rerun by this checker.')
def check():
    bundle=read('portable-files.json')
    assert bundle['original_stage_manifest_sha256']==sha(H/'portable-final-receipt.json')
    assert all('__pycache__' not in x['path'] and not x['path'].endswith(('.pyc','.pyo')) for x in bundle['files'])
    for item in bundle['files']:
        path=H/'reproduction'/item['path'];assert path.is_file() and path.stat().st_size==item['bytes'] and sha(path)==item['sha256'],item['path']
    assert bundle['derived_arrays_or_full_texts_included'] is False
    assert bundle['manuscript_target_rerun'] is False
    original=read('reproduction/receipt.json')
    assert sha(H/'reproduction/receipt.json')==bundle['scientific_receipt_sha256']
    for item in original['files']:assert sha(H/'reproduction'/item['path'])==item['sha256']
    assert read('results.json')==expected_results()
    control=read('reproduction/independent-controls.json')
    assert control['independent_offset_counts']==103995 and len(control['cases'])==9
    t0=read('reproduction/positive_control_T0.json')['results']
    plants=[x for x in t0 if x['truth']]
    assert len(plants)==4 and all(x['text']==x['truth']['text'] and x['offset']==x['truth']['offset'] for x in plants)
    assert [round(x['best']) for x in plants]==[2506,2928,2506,2928]
    assert len(read('reproduction/independent-t0-audit.json')['witnesses'])==6
    parity=read('reproduction/portable-offline-tests.json')
    assert parity['corpus_arrays_equal']==94 and parity['manuscript_arrays_equal']==2 and parity['fixture_offset_values']==34665
    assert parity['network_calls']==0 and parity['temporary_corpus_removed'] and not parity['manuscript_target_rerun']
    shape=read('input-shape-check.json');m=read('reproduction/inputs-frozen.json')['manuscript']
    assert shape['lengths_sha256']==m['lengths_sha256'] and shape['fcounts_sha256']==m['fcounts_sha256']
    assert shape['observed_outside_source_masks_1_to_29']==0 and shape['observed_max']==14
    from plot import render
    assert (H/'length-matches.svg').read_bytes()==render()
    svg=ET.fromstring((H/'length-matches.svg').read_bytes())
    assert float(svg.attrib['width'])<=600
    assert all(float(x.attrib['font-size'])>=30 for x in svg.iter() if 'font-size' in x.attrib)
    print('PASS: 40 source/evidence bundle files, frozen science, 84/94 eligibility, 21 winner receipts, controls and figure; no corpus scan run.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.parse_args();check()
