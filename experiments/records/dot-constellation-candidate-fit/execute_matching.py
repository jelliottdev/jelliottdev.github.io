"""Execute the reviewed fixed geometry grid; --check never writes expectations."""
import argparse
import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np
from similarity import Library, PERMUTATIONS

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def verify():
    plan = read(HERE / 'matching-plan-frozen.json')
    for item in plan['inputs']:
        assert sha(HERE / item['path']) == item['sha256'], item['path']
    authorization = read(HERE / 'execution-authorization.json')
    assert sha(HERE / 'matching-plan-frozen.json') == authorization['plan_sha256']
    assert sha(HERE / 'pretarget-gate.json') == authorization['gate_sha256']
    for name, digest in authorization['additional_code_sha256'].items():
        assert sha(HERE / name) == digest, name
    gate = read(HERE / 'pretarget-gate.json')
    assert gate['plan_sha256'] == authorization['plan_sha256']
    assert gate['all_exact_true_candidates_in_tie_set']
    assert gate['exact_plants'] == 88 and gate['noisy_plants'] == 1408
    assert gate['maximum_svd_score_delta'] <= 1e-12
    assert not gate['target_scores_computed'] and gate['null_reference_queries_computed'] == 0
    return authorization


def project(stars):
    """Same fixed J2000 gnomonic rule as the approved candidate preparation."""
    ra = np.radians([s['ra_j2000_deg'] for s in stars])
    dec = np.radians([s['dec_j2000_deg'] for s in stars])
    vectors = np.column_stack([np.cos(dec)*np.cos(ra), np.cos(dec)*np.sin(ra), np.sin(dec)])
    centre = vectors.mean(axis=0)
    if np.linalg.norm(centre) <= 1e-12:
        return None
    centre /= np.linalg.norm(centre)
    ra0, dec0 = np.arctan2(centre[1], centre[0]), np.arcsin(centre[2])
    east = np.array([-np.sin(ra0), np.cos(ra0), 0])
    north = np.array([-np.sin(dec0)*np.cos(ra0), -np.sin(dec0)*np.sin(ra0), np.cos(dec0)])
    den = vectors @ centre
    if np.any(den <= 0):
        return None
    points = np.column_stack([(vectors @ east)/den, (vectors @ north)/den])
    return points if np.all(np.isfinite(points)) and np.sum((points-points.mean(axis=0))**2) > 0 else None


def stable_best(scores, names):
    minimum = float(scores.min())
    tied = np.argwhere(scores <= minimum + 1e-12)
    # Library order is IAU shortname; permutation order is lexicographic;
    # orientation preserving precedes reflection, as frozen before target.
    chosen = tied[0]
    return minimum, chosen, sorted({names[int(row[0])] for row in tied})


def target_result(page, query, library):
    scores = library.all_scores(query)
    minimum, chosen, ties = stable_best(scores, library.names)
    rows = []
    minima = scores.min(axis=(1, 2))
    for i, name in enumerate(library.names):
        own_min = float(minima[i])
        own_ties = np.argwhere(scores[i] <= own_min + 1e-12)
        permutation, orientation = own_ties[0]
        witness = library.witness(query, i, int(permutation), int(orientation))
        assert abs(witness['normalized_rms']-own_min) < 1e-12
        rows.append({'constellation': name, 'rank': 1+int(np.sum(minima < own_min-1e-12)),
                     'score': own_min, 'optimum_label_ties': own_ties.tolist(), 'witness': witness})
    return {'page': page, 'role': 'primary' if page == 'lp2-07' else 'dependent repeat-artwork robustness',
            'query_points_pixels': np.asarray(query).tolist(), 'best_score': minimum,
            'best_constellation_ties': ties,
            'best_witness': library.witness(query, *[int(x) for x in chosen]),
            'candidate_minima': rows}, scores


def reference(kind, library, membership):
    seed = 330120261025 if kind == 'uniform_disk' else 330120261026
    rng = np.random.Generator(np.random.PCG64(seed))
    groups = [[s for s in membership if s['constellation'] == name] for name in library.names]
    outcomes, rejected = [], []
    started = time.perf_counter()
    for ordinal in range(4095):
        for attempt in range(100):
            if kind == 'uniform_disk':
                angles = rng.uniform(0, 2*np.pi, 5)
                radii = np.sqrt(rng.uniform(0, 1, 5))
                query = np.column_stack([radii*np.cos(angles), radii*np.sin(angles)])
                metadata = {}
            else:
                origin = int(rng.integers(88))
                indices = rng.choice(len(groups[origin]), 5, replace=False)
                stars = [groups[origin][int(i)] for i in indices]
                query = project(stars)
                metadata = {'origin_constellation': library.names[origin], 'HRs': [s['HR'] for s in stars]}
            if query is not None and np.sum((query-query.mean(axis=0))**2) > 0:
                break
            rejected.append({'ordinal': ordinal, 'attempt': attempt, **metadata,
                             'reason': 'undefined_or_nonfront_gnomonic_projection_or_exact_zero_radius'})
        else:
            raise RuntimeError('Frozen 100-attempt reference cap reached')
        scores = library.all_scores(query)
        minimum, chosen, ties = stable_best(scores, library.names)
        outcomes.append({'ordinal': ordinal, 'attempt': attempt, **metadata,
                         'query_points': query.tolist(), 'minimum': minimum,
                         'best_constellation_ties': ties, 'best_label': chosen.tolist()})
    return {'generator': kind, 'seed': seed, 'queries': 4095, 'rejected_attempts': rejected,
            'outcomes': outcomes, 'runtime_seconds': time.perf_counter()-started}


def comparison(values, threshold):
    n = len(values)
    k = int(np.sum(np.asarray(values) <= threshold))
    p, z = k/n, 1.959963984540054
    centre = (p+z*z/(2*n))/(1+z*z/n)
    half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return {'count_at_or_below': k, 'trials': n, 'plus_one_fraction': (k+1)/(n+1),
            'monte_carlo_wilson95_for_generator_fraction': [max(0, centre-half), min(1, centre+half)]}


def execute():
    authorization = verify()
    started = time.perf_counter()
    candidates = read(HERE / 'constellation-candidates.json')
    library = Library([r['gnomonic_xy'] for r in candidates], [r['constellation'] for r in candidates])
    # First real geometry load occurs only after frozen-code/input verification.
    geometry = read(HERE / 'inputs/five-dot-geometry.json')
    targets, scores = [], []
    target_started = time.perf_counter()
    for page in ['lp2-07', 'lp2-23', 'lp2-56']:
        region = next(r for r in geometry['regions'] if r['page'] == page)
        query = np.asarray([c['centroid'] for c in region['components']])
        assert query.shape == (5, 2)
        result, all_scores = target_result(page, query, library)
        result['frozen_region'] = {k: region[k] for k in ['rect', 'image_sha256']}
        targets.append(result)
        scores.append(all_scores)
    target_seconds = time.perf_counter()-target_started
    membership = read(HERE / 'catalogue-membership.json')
    references = [reference(kind, library, membership) for kind in ['uniform_disk', 'catalogue_sets']]
    for target in targets:
        for row in target['candidate_minima']:
            row['full_selection_references'] = {
                ref['generator']: comparison([o['minimum'] for o in ref['outcomes']], row['score'])
                for ref in references}
    result = {'plan_sha256': authorization['plan_sha256'],
              'authorization_sha256': sha(HERE / 'execution-authorization.json'),
              'registrations_per_query': 21120, 'primary_page': 'lp2-07',
              'dependent_robustness_pages': ['lp2-23', 'lp2-56'],
              'target_queries': 3, 'reference_queries': 8190,
              'target_registration_scores': 63360, 'reference_registration_scores': 172972800,
              'targets': targets,
              'reference_summary': [{k: v for k, v in ref.items() if k != 'outcomes'} for ref in references],
              'runtime_seconds': {'targets': target_seconds, 'total': time.perf_counter()-started}}
    return result, references, np.asarray(scores)


def deterministic(value):
    if isinstance(value, dict):
        return {k: deterministic(v) for k, v in value.items() if k not in ['runtime_seconds']}
    if isinstance(value, list):
        return [deterministic(v) for v in value]
    return value


def close(actual, expected, path='root'):
    if isinstance(expected, dict):
        assert actual.keys() == expected.keys(), path
        for key in expected:
            close(actual[key], expected[key], path+'.'+key)
    elif isinstance(expected, list):
        assert len(actual) == len(expected), path
        for i, (a, b) in enumerate(zip(actual, expected)):
            close(a, b, path+f'[{i}]')
    elif isinstance(expected, float):
        assert math.isclose(actual, expected, abs_tol=1e-12, rel_tol=1e-12), path
    else:
        assert actual == expected, path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result, references, scores = execute()
    if args.check:
        close(deterministic(result), deterministic(read(HERE / 'matching-results.json')))
        close(deterministic(references), deterministic(read(HERE / 'reference-results.json')))
        assert np.allclose(scores, np.load(HERE / 'target-scores.npy'), atol=1e-12, rtol=1e-12)
        print('PASS: full frozen target and 8,190 reference queries match deterministic saved outputs; no writes')
    else:
        assert not (HERE / 'matching-results.json').exists(), 'Never overwrite frozen scientific results'
        write(HERE / 'matching-results.json', result)
        write(HERE / 'reference-results.json', references)
        np.save(HERE / 'target-scores.npy', scores)
        print(json.dumps({'target_runtime_seconds': result['runtime_seconds']['targets'],
                          'reference_runtime_seconds': [r['runtime_seconds'] for r in references],
                          'best_primary': result['targets'][0]['best_witness']}))


if __name__ == '__main__':
    main()
