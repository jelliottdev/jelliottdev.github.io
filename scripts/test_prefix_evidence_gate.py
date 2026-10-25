"""Exhaustive causal tests on synthetic streams; no manuscript target decode."""
import itertools
from prefix_evidence_gate import inverse_affine_prefix, first_mismatch, reset_prefix_compatibility


def run():
    checked = 0
    # Every three-symbol ciphertext, two-symbol key, reset location and opening.
    # Directly compare the actually reset decoder with the proposed rejection.
    for modulus in (2, 3):
        sequences = list(itertools.product(range(modulus), repeat=3))
        for cipher in sequences:
            for key in itertools.product(range(modulus), repeat=2):
                baseline = [(c-key[i % 2]) % modulus for i,c in enumerate(cipher)]
                for boundary in (None, 1, 2, 3):
                    reset = [(c-key[(i if boundary is None or i < boundary else i-boundary) % 2]) % modulus
                             for i,c in enumerate(cipher)]
                    for opening in sequences:
                        mismatch = next((i for i in range(3) if baseline[i] != opening[i]), None)
                        assert first_mismatch(baseline, opening) == mismatch
                        excluded = reset_prefix_compatibility(mismatch, boundary)
                        assert excluded == (mismatch is not None and (boundary is None or mismatch < boundary))
                        if excluded:
                            assert reset != list(opening), (cipher,key,boundary,opening)
                        if reset == list(opening):
                            assert not excluded
                        checked += 1
    # Equality is deliberately retained: changing the reset can repair that rune.
    assert not reset_prefix_compatibility(1,1)
    assert reset_prefix_compatibility(0,1)
    assert not reset_prefix_compatibility(None,None)
    assert reset_prefix_compatibility(0,None)
    assert first_mismatch([1,2,3],[1,2]) is None
    assert first_mismatch([1,2,3],[1,0]) == 1
    for args in (([0],0,0,29),([0],2,0,4),([29],1,0,29),([],1,0,29),([True],1,0,29),([0],True,0,29),([0],1,0,1)):
        try:
            inverse_affine_prefix(*args)
        except ValueError:
            pass
        else:
            raise AssertionError(('Invalid affine input accepted',args))
    for args in ((-1,None),(True,None),(0,-1),(0,True)):
        try:
            reset_prefix_compatibility(*args)
        except ValueError:
            pass
        else:
            raise AssertionError(('Invalid reset evidence accepted',args))
    affine = 0
    for modulus in (2,3,5,7):
        for a in range(1,modulus):
            for b in range(modulus):
                for output in itertools.product(range(modulus), repeat=2):
                    transformed = [(a*x+b) % modulus for x in output]
                    for desired in itertools.product(range(modulus), repeat=2):
                        required = inverse_affine_prefix(list(desired),a,b,modulus)
                        # A bijection preserves the exact position of disagreement.
                        assert first_mismatch(transformed,desired) == first_mismatch(output,required)
                        affine += 1
    print(f'PASS: {checked} exhaustive synthetic reset/opening cases and {affine} affine mismatch cases; strict reset equality survives.')
    rejection_checks()


def rejection_checks():
    """Mutate saved evidence in memory/temp files; preserve all real source bytes."""
    import copy
    import contextlib
    import importlib.util
    import io
    import json
    import tempfile
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    folder = root/'experiments/records/prepared-opening-evidence-gates'
    spec = importlib.util.spec_from_file_location('independent_prefix_checker',folder/'check.py')
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    original_read = checker.read
    original_report = json.loads((folder/'results.json').read_bytes())
    failures = 0
    with tempfile.TemporaryDirectory(prefix='prefix-evidence-negative-') as directory:
        temporary = Path(directory)
        (temporary/'plan.json').write_bytes((folder/'plan.json').read_bytes())
        checker.HERE = temporary
        def rejects(report, replacement=None):
            nonlocal failures
            (temporary/'results.json').write_text(json.dumps(report),encoding='utf-8')
            checker.read = original_read if replacement is None else replacement
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    checker.check()
            except (AssertionError,KeyError,TypeError,ValueError,IndexError):
                failures += 1
            else:
                raise AssertionError('Malformed evidence was accepted')
        mutations = [
            lambda r:r['recipes'].pop(),
            lambda r:r['recipes'].append(copy.deepcopy(r['recipes'][0])),
            lambda r:r['recipes'][0]['pages'].pop(),
            lambda r:r['recipes'][0]['pages'].append(copy.deepcopy(r['recipes'][0]['pages'][0])),
            lambda r:r['recipes'][0]['pages'][0].update(first_changed_reset={'rune_offset':0,'character_offset':0}),
            lambda r:r['recipes'][0]['pages'][0].update(first_mismatch_zero_based=True),
            lambda r:r['recipes'][2]['pages'][0].update(saved_output_prefix=[29]),
            lambda r:r.update(opening_indices=[0]*24),
            lambda r:r.update(plan_sha256='0'*64),
        ]
        for mutate in mutations:
            report = copy.deepcopy(original_report)
            mutate(report)
            rejects(report)
        row_path = 'experiments/records/lp2-row-column-routes/results.json'
        word_path = 'experiments/records/lp2-word-reversal/results.json'
        census_path = 'experiments/suites/feedback-opening-census/cases.json'
        source_mutations = [
            (row_path,lambda r:r['pages'].pop()),
            (row_path,lambda r:r['pages'].append(copy.deepcopy(r['pages'][0]))),
            (row_path,lambda r:r['pages'][0]['cases'].pop()),
            (row_path,lambda r:r['pages'][0]['cases'][0]['output_indices'].__setitem__(0,29)),
            (word_path,lambda r:r['pages'][0]['cases'].append(copy.deepcopy(r['pages'][0]['cases'][0]))),
            (census_path,lambda r:r['cases'].append(copy.deepcopy(r['cases'][0]))),
        ]
        for path,mutate in source_mutations:
            value = copy.deepcopy(original_read(path))
            mutate(value)
            def substituted(relative, value=value, path=path):
                return value if relative == path else original_read(relative)
            rejects(original_report,substituted)
    checker.read = original_read
    print(f'PASS: {failures} malformed report/source-structure rejection cases; real manuscript and saved source files unchanged.')


if __name__ == '__main__':
    run()
