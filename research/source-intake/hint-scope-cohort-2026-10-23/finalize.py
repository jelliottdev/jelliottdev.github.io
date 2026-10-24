"""Save evidence pins and proposed reconciliation rows without shared registry edits."""
import hashlib,json,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;S=H.parents[3]/'source-cache/dukotah-cicada3301'
REV='f08b20b632d91209ddbaa747e8e2f23df0c78ba1'
selection=json.loads((H/'selection.json').read_text())
evidence={
 'F-02':['research/ROUND-9-RESULTS.md','research/DEAD_ENDS.md'],
 'B-06':['PICKUP-HERE.md'], 'B-07':['PICKUP-HERE.md'],
 'B-15':['research/LEDGER.md','research/DEAD_ENDS.md','liber-primus/analysis/R6_TRANSITION_STRUCTURE.txt'],
 'B-19':['research/ROUND-9-RESULTS.md','liber-primus/analysis/skeleton/length_anomaly.py','liber-primus/analysis/skeleton/length_anomaly.json'],
 'B-20':['research/DEAD_ENDS.md','liber-primus/analysis/direction/direction.py','liber-primus/analysis/direction/direction_results.json'],
 'B-24':['research/LEDGER.md','liber-primus/analysis/r2_fractionation_signature.py','liber-primus/analysis/r2_frac_out.txt'],
 'C-01':['PICKUP-HERE.md','research/ROUND-8-RESULTS.md','liber-primus/analysis/round10/L4-skeleton/RESULTS.md','liber-primus/analysis/round10/L4-skeleton/scan_results.json','liber-primus/analysis/round10/L4-skeleton/positive_control_T0.json']}
pins=[]
for name in sorted(set(sum(evidence.values(),[]))):
    raw=(S/name).read_bytes()
    assert raw==subprocess.check_output(['git','-C',str(S),'show',f'{REV}:{name}'])
    pins.append(dict(path=name,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
specs={
 'F-02':('source-proposal-only',
    'The pinned Round-9 report expressly leaves words/map and meaning/road uninterpreted. It specifies no executable rule for either clause. Its numbers/direction branch is the separate B-20 grid.',
    ['No frozen map/road transform, selection function, output criterion or model is supplied by this entry.','Uniqueness of the signed methodological hint is a source characterization, not established by this review.','A concrete new map/road rule remains open; source-entry review does not interpret the clue.']),
 'B-06':('source-proposal-only',
    'This is a reopening condition: an externally evidenced pointer naming a key text. The entry supplies no such pointer or fixed key to execute.',
    ['An archival/signed pointer and its fixed text are not supplied; arbitrary candidate texts are a different experiment.','No archive or people investigation was undertaken, and no whole keytext class is excluded.']),
 'B-07':('source-proposal-only',
    'This is a reopening condition requiring a correctly targeted, locally held archive containing the AN END referent; no concrete candidate archive is supplied by the entry.',
    ['The target bytes and correct archival linkage are absent from the proposal.','This review does not establish that no archive exists or exclude a hash preimage.']),
 'B-15':('unsupported-source-verdict',
    'The source table itself says trigram-tensor chi-square is INCONCLUSIVE at 0.531 counts/cell. Powered offset/entropy/zero-cell arms have narrower negative results. Broad transition-family closure does not follow from the sparse tensor arm.',
    ['No fresh transition null simulation was run here.','Trigram/second-order structure beyond the tested powered summaries remains open; more cells do not create more observations.']),
 'B-19':('partial',
    'Fresh exact-source local LENGTH replay reproduces 2,928 words, 12,956 runes and 458 F. Independently checked 11,274 sampled passages in the two available eligible texts: zero reach either endpoint 4.268443 or 4.424863. This cannot reproduce the archived 44/47 lower-endpoint count.',
    ['The original 47-text LENGTH corpus is absent; local KJV and self_reliance are a strict subset.','The archived 44/47 statistic tests the all-F-null lower endpoint, not the observed upper point.','No null rate, p-value or global non-anomaly conclusion follows from two local comparison texts.','Source excludes the final valid passage start and samples long texts rather than testing every start; this replay preserves that behavior.']),
 'B-20':('blocked-exact-replay',
    'Exact source code fixes 2,670 readings per stream: 400-rune walk caps, starts 64/32/16 by family, and six shuffled-stream maxima. Archived best is -16.080036; missing seed_sweep/ngram.bin prevents exact language-score replay.',
    ['seed_sweep/ct.bin is also absent; a reconstructed target could be checked separately, but would not supply the missing model.','No changed scorer was substituted and no archived score is labeled a fresh target test.','Unspecified starts, longer reads and new justified direction rules remain outside this finite grid.']),
 'B-24':('unsupported-source-verdict',
    'Source explicitly labels AN END 85-rune specificity control underpowered. Its decision instead relies on a length-matched synthetic period control and corpus-matched surrogate null; AN END alone cannot validate specificity or universal fractionation closure.',
    ['No fresh 10,000-surrogate fractionation replay was run here.','Period/packing models outside lags 2-40 and the three fixed decompositions remain open.','The source synthetic positive-control pass does not repair all possible alternatives or make the 85-rune specificity arm well-powered.']),
 'C-01':('partial',
    'The never-extended premise is superseded in the same pinned source: Round-10 L4 scanned 224 texts/22,643,594 words, with exact/slack1/interval bests inside shuffled bands. Fresh exact-source scanner controls recover 9/9 interval plants at W=120/400/2928 and match all 69,330 per-offset counts to independent direct calculations.',
    ['The 224-text corpus scan and archived detection-floor experiment were not freshly replayed.','Fresh synthetic controls validate these scanner cases, not the missing corpus bytes or the archived negative scores.','An entire Gutenberg mirror, unheld corpora, different recensions and word insertions/deletions remain outside this result.','Original 51-text scan and later 224-text extension must not be counted as new local tests.'])}
rows=[]
for item in selection['entries']:
    i=item['source_id'];status,verified,unresolved=specs[i]
    row=dict(source_id=i,source_claim=item['claim'],status=status,record_links=[],
        source_evidence=evidence[i],verified_subclaim=verified,unresolved_parts=unresolved,
        whole_entry_coverage_verified=False)
    if i in ['B-19','C-01']:
        row['execution_replay']=dict(state='partial-execution',record_ids=[],
          scope='Bounded local LENGTH subset at both endpoints.' if i=='B-19' else 'Fresh synthetic controls of exact L4 blocked FFT scanner; no target corpus replay.',wider_method_excluded=False)
    rows.append(row)
(H/'evidence-pins.json').write_text(json.dumps(dict(source_revision=REV,inputs=pins),indent=2)+'\n',encoding='utf-8')
(H/'proposed-reconciliation.json').write_text(json.dumps(dict(schema='liberpedia-hint-scope-review-v1',initial_reviews=8,new_public_records=0,new_target_runs=1,new_synthetic_control_grids=1,entries=rows),indent=2)+'\n',encoding='utf-8')
print('Pinned',len(pins),'source files; saved 8 scoped review proposals. No shared registry modified.')
