"""Run the frozen rotating/folded GP29 key-schedule census."""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'experiments/suites/classical-key-schedules'))
from engine import run  # noqa: E402


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = run(HERE.name)
    path = HERE / 'results.json'
    if args.check:
        assert result == json.loads(path.read_text(encoding='utf-8'))
    else:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(HERE.name, result['configuration_count'], result['exact_matches'])
