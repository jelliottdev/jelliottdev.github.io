"""Execute preserved Step 0 unchanged in an isolated, offline input tree."""
import json,shutil,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as td:
 lp=Path(td)/'liber-primus'; lane=lp/'analysis/round24/C8-date-indexed-pad'; lane.mkdir(parents=True); (lp/'data').mkdir()
 for src,target in [('source-step0.py',lane/'step0_timestamps.py'),('source-lp.md',lp/'data/scream314_lp.md'),('source-runes.txt',lp/'data/krisyotam_runes.txt')]:shutil.copyfile(HERE/src,target)
 subprocess.run(['python',str(lane/'step0_timestamps.py')],check=True,capture_output=True,text=True)
 fresh=json.loads((lane/'cache/timestamps.json').read_bytes())
 assert fresh==json.loads((HERE/'source-replay.json').read_bytes())
subprocess.run(['python',str(HERE/'check.py')],check=True)
