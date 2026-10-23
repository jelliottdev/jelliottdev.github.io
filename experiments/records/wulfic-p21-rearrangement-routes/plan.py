"""Freeze the archived P21–30 rearrangement grid before manuscript scoring."""
import hashlib
import json
import pathlib
import subprocess

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SOURCE=ROOT.parent/'source-archives'/'Wulfic-Cicada3301-Liber_Primus'
REV='bf89d3d13aad2b8f2c95ab195cf1b092f250775c'
FILES=['tools/legacy/p21_30_rearrange.py','data/corpora/wordlist.txt']+[f'pages/page_{p:02d}/runes.txt' for p in range(21,31)]
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(rel):return subprocess.check_output(['git','-C',str(SOURCE),'show',REV+':'+rel])

def main():
    assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD']).decode().strip()==REV
    plan={
      'schema':'liberpedia-wulfic-p21-rearrangement-plan-v1',
      'timing':'retrospective source replay; source code and existing related record read before grid frozen, manuscript outcomes not yet computed by this record',
      'source_revision':REV,
      'source_url':'https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/'+REV+'/tools/legacy/p21_30_rearrange.py',
      'source_files':{rel:{'sha256':sha(blob(rel)),'bytes':len(blob(rel))} for rel in FILES},
      'site_pages':{f'lp2-{p-17:02d}':sha((ROOT/f'data/pages/lp2-{p-17:02d}.json').read_bytes()) for p in range(21,31)},
      'page_mapping':'source old pages21–30 map to current LP2-04–13, exact flat rune parity required',
      'source_grid':'Run exact source run_tests 45 route outputs for each of ten page-assigned keyword/modes, including subset extraction, full-length rune rearrangements and word rearrangements. Include unmodified keyword-only baseline separately.',
      'scoring':'source score_text against committed wordlist with source branch-specific text construction; no alternative spacing inserted into flat rune routes',
      'null':'199 seeded trials; shuffle each source page rune sequence within that page while preserving its exact separator skeleton, share each shuffled page across all 45 routes, and retain whole-ten-page maximum source word score. Seed 20261023.',
      'controls':'On LP2-04 source word skeleton, fill every word length from lexicographically first compatible pinned wordlist item (I for a one-rune gap); verify complete inverse+forward roundtrip under source assigned keyword and reverse route. Compare source word score for the exact same known plaintext with and without spaces; expect source flat route ranking limitation if unbroken multiword text scores zero. Check all full-length route multisets/IoC and all word-order scores as mathematical invariants on every actual page.',
      'source_original':'Stage exact Git blobs under original legacy-relative paths and execute unmodified script. Compare reported top rows and no-word verdict with independent replay.',
      'interpretation':'Word ordering and full-length rune permutation cannot change rune frequency/IoC. Extraction is shorter and excluded from that invariant. Reordering whole words cannot change the source matched-word score; within-word changes can. Any gate failure is a scorer limitation, not proof against a transposition.',
      'overlap':'Published wulfic-keyed-transposition-cohort runs a different source file, transposition_solver.py, with different route grid and fallback word scorer. This record is only p21_30_rearrange.py.'}
    (HERE/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    print(sha((HERE/'plan.json').read_bytes()))

if __name__=='__main__':main()
