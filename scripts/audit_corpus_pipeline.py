"""Check two pinned historical corpus-code defects with small synthetic inputs.

Supply the directory containing project_runeberg.py and
project_runeberg_statistics.py. No corpus, third-party imports or plotting runs.
Only the two inspected arithmetic functions are extracted for execution.
"""
import argparse
import ast
import copy
import hashlib
import inspect
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {'project_runeberg.py': '8f9b13baf941f2d34579d725a3d05bb08673a547',
            'project_runeberg_statistics.py': '1e8b9088f8888b10cdfe828331c9a5953fa362f7'}


class Values(list):
    def mean(self):
        return sum(self)/len(self)

    def __le__(self, other):
        return [value <= other for value in self]


def frame(values):
    return {'length_2': SimpleNamespace(values=Values(values))}


def audit(directory):
    trees, sources = {}, []
    for name, oid in EXPECTED.items():
        raw = (directory/name).read_bytes()
        actual = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        assert actual == oid, 'Pinned source differs: '+name
        trees[name] = ast.parse(raw.decode('utf-8'))
        sources.append({'file': name, 'git_blob': oid, 'sha256': hashlib.sha256(raw).hexdigest()})
    corpus = trees['project_runeberg.py']
    target = next(n for n in corpus.body if isinstance(n, ast.FunctionDef) and n.name == 'process_word_counts')
    signature = inspect.Signature([inspect.Parameter(a.arg, inspect.Parameter.POSITIONAL_OR_KEYWORD) for a in target.args.args])
    caller = next(n for n in corpus.body if isinstance(n, ast.FunctionDef) and n.name == 'create_results')
    call = next(n for n in ast.walk(caller) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == target.name)
    try:
        signature.bind(*[None]*len(call.args))
    except TypeError as error:
        binding_error = str(error)
    else:
        raise AssertionError('Expected missing argument was not detected')
    assert binding_error == "missing a required argument: 'word_count'"
    signature.bind(None, None, 2902)

    functions = [n for n in trees['project_runeberg_statistics.py'].body
                 if isinstance(n, ast.FunctionDef) and n.name in ('empirical_p_value', 'check_empirical_p')]
    assert len(functions) == 2
    namespace = {}
    exec(compile(ast.Module(body=functions, type_ignores=[]), '<pinned arithmetic functions>', 'exec'), namespace)
    supplied = frame([1, 2, 3])
    observation = SimpleNamespace(loc={('unsolved', 'length_2'): 2})
    try:
        namespace['check_empirical_p'](supplied, observation, 'length_2')
    except NameError as error:
        missing_global = error.name
    else:
        raise AssertionError('Expected missing global was not detected')
    assert missing_global == 'pg_df'
    namespace['pg_df'] = frame([9, 9, 9])
    original = namespace['check_empirical_p'](supplied, observation, 'length_2')
    assert original == (0, 2, 9)

    repaired = copy.deepcopy(functions)
    target = next(n for n in repaired if n.name == 'check_empirical_p')
    for node in ast.walk(target):
        if isinstance(node, ast.Name) and node.id == 'pg_df':
            node.id = 'pr_df'
    namespace2 = {'pg_df': frame([9, 9, 9])}
    exec(compile(ast.Module(body=repaired, type_ignores=[]), '<parameter repair>', 'exec'), namespace2)
    fixed = namespace2['check_empirical_p'](supplied, observation, 'length_2')
    assert fixed == (2/3, 2, 2)
    return {'source_revision': 'cb5cdb908bb34b68d8a05353eaace56e83d0bbf2', 'sources': sources,
            'missing_argument': {'call_line': call.lineno, 'error': binding_error, 'three_argument_binding_passes': True},
            'global_variable': {'missing_global': missing_global, 'supplied_distribution': [1,2,3],
                                'conflicting_global_distribution': [9,9,9], 'threshold': 2,
                                'original_tail_threshold_mean': original, 'repaired_tail_threshold_mean': fixed},
            'scope': 'Two source-level defects and synthetic regression checks only. No corpus statistics, plots, or historical probability claims reproduced. Synthetic values are arbitrary units, not manuscript proportions.',
            'repair': 'Pass word_count at the process_word_counts call; use pr_df inside check_empirical_p. The latter repair changes the extracted test function only, not the archived source.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_directory', type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    report = audit(args.source_directory)
    # Normalize tuples to JSON arrays for exact saved-report comparison.
    report = json.loads(json.dumps(report))
    path = ROOT/'exports/corpus-pipeline-audit.json'
    if args.write:
        path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    else:
        assert json.loads(path.read_bytes()) == report
    print('PASS: pinned sources, missing-argument binding, global-variable failure and synthetic parameter repair')
