"""Write the catalog envelope after all experiment artifacts are frozen."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ID="wulfic-p08-hint-grid-keys"
PREFIX=f"experiments/records/{ID}/"
def h(name):return hashlib.sha256((HERE/name).read_bytes()).hexdigest()
def ref(name):return {"path":PREFIX+name,"sha256":h(name)}

def main():
    r=json.loads((HERE/"results.json").read_text(encoding="utf-8"))
    d=json.loads((HERE/"diagnostic-results.json").read_text(encoding="utf-8"))
    assert r["summary"]["sweep_gate_hits"]==103 and d["observed_lp2_gate_hits"]==4
    obj={
      "id":ID,"status":"draft","title":"P08 hint-grid keys against LP2","question":"Do the fixed, repeated keys derived from the solved P08 hint grid pass the source's frequency screen on LP2 pages?",
      "reader_question":"Can the earlier hint grid serve as a repeating key for Liber Primus?",
      "summary":"The source's grid matches the saved LP1-08 OutGuess payload. Its old page range includes nine solved LP1 pages, where 99 of 103 phase-sweep threshold hits occur. Four hits on LP2-32 reduce to two frequency relations and no independently checked reading.",
      "finding":"Across 17,766 source-specified rotated-key cases, 99 of 103 IoC>1.25 hits are on solved LP1 pages. The four LP2 hits are all on LP2-32; three are algebraically related. A retrospective LP2-only shared-shuffle diagnostic has 0/199 maxima at the observed 1.382, but does not identify a reading or cipher.",
      "limitations":"This is a corrected-path adaptation: the source script points at nonexistent tools/pages. The original old P08–54 range covers LP1-08–16 and LP2-00–37 only. The source screen tests rune frequency, not readable text. The LP2-only comparison was selected after inspecting the LP1/LP2 split; conditional shuffles and 199 trials do not account for the wider historical choice of clue interpretations and key families.",
      "next_steps":"Require a fixed full-page decoding rule with preserved word structure and a held-out prediction before treating a grid-derived key as a reading.",
      "outcome":"inconclusive","tags":["LP2","source adaptation","P08 hint","running key","frequency screen","negative control"],
      "scope":{"pages":[f"lp1-{i:02d}" for i in range(8,17)]+[f"lp2-{i:02d}" for i in range(38)],"artifacts":[PREFIX+"plan.json",PREFIX+"source-pages.json",PREFIX+"diagnostic-plan.json","experiments/records/outguess-default-key/results/lp1-08.bin"],"representation":"Exact committed Wulfic page_08–54 rune files, mapped to current LP1-08–16 and LP2-00–37; 14/28-value keys from source-embedded hint pairs independently matched to the saved LP1-08 OutGuess bytes.","procedure":"Verify source-grid rows against the 140-byte LP1-08 payload; correct the legacy page path, replay seven unrotated keys and five keys at all rotations in three GP29 modes using the source IoC/singleton gates; encrypt known LP1 readings as positive controls; shuffle each source page 199 times and repeat the whole phase sweep.","parameters":"47 pages; 987 fixed and 17,766 rotated-key cases; 510 planted transforms; source fixed IoC>1.3 or IoC>1.15 with singletons I/A, rotated IoC>1.25; 199 shared page shuffles. A later LP2-only readout uses the same random stream.","exclusions":"Other grid interpretations, bigram substitution, Koan-text keys, later LP2 pages, non-GP29 encodings, alternative word scoring and any broader historical idea search."},
      "review":{"kind":"pinned public-source corrected-path adaptation with independently verified carrier bytes, observed cases and planted controls","retested_on":"2026-10-23","reviewer":"LP1-08 extracted rows match the source literal exactly; all 47 raw page arrays, source-row key arithmetic, 18,753 observed scores and 510 planted recoveries independently checked; complete seeded null recomputes in run.py and diagnostic.py","human_review":"pending"},
      "reproduction":{"command":f"python {PREFIX}run.py --check && python {PREFIX}diagnostic.py --check && python {PREFIX}check.py && python {PREFIX}check_carrier.py --check && python {PREFIX}plot.py --check","environment":"Python 3 with NumPy; source page bytes and the archived 140-byte LP1-08 extraction are bundled, so the external sparse Git checkout is not required to rerun the adaptation.","script":PREFIX+"run.py","script_sha256":h("run.py"),"inputs":[ref(x) for x in ["plan.json","source-pages.json","diagnostic-plan.json","prepare.py","run.py","diagnostic.py","check.py","check_carrier.py","plot.py","make_record.py"]]+[{"path":str(p.relative_to(ROOT)).replace('\\','/'),"sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in [ROOT/"experiments/records/outguess-default-key/plan.json",ROOT/"experiments/records/outguess-default-key/results/report.json",ROOT/"experiments/records/outguess-default-key/results/lp1-08.bin"]],"outputs":[ref(x) for x in ["results.json","diagnostic-results.json","carrier-audit.json","comparison.svg"]]},
      "sources":[{"label":"Wulfic P08 grid analysis at pinned revision","url":"https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/p08_grid_analysis.py"}],
      "related":["solved-reading-running-key","wulfic-native-key-streams","lp2-row-column-routes"],
      "visuals":[{"path":PREFIX+"comparison.svg","caption":"Most source threshold hits occur on solved LP1 pages; the four LP2 hits share only two frequency relations and have no verified plaintext."}]
    }
    (HERE/"record.json").write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
    print("Wrote",ID)
if __name__=="__main__":main()
