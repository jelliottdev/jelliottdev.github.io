"""Independent target SVD, saved-reference counts, and fixed reference samples."""
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
from svd_reference import all_scores

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def main():
    plan = read('matching-plan-frozen.json')
    for item in plan['inputs']:
        assert hashlib.sha256((HERE/item['path']).read_bytes()).hexdigest() == item['sha256']
    candidates = read('constellation-candidates.json')
    names = [r['constellation'] for r in candidates]
    points = np.asarray([r['gnomonic_xy'] for r in candidates])
    saved = read('matching-results.json')
    references = read('reference-results.json')
    stored_scores = np.load(HERE/'target-scores.npy')
    permutations = list(itertools.permutations(range(5)))
    maximum_delta = 0
    for ordinal, target in enumerate(saved['targets']):
        query = np.asarray(target['query_points_pixels'])
        scores = all_scores(points, query)
        maximum_delta = max(maximum_delta, float(np.max(np.abs(scores-stored_scores[ordinal]))))
        assert np.allclose(scores, stored_scores[ordinal], atol=1e-12, rtol=0)
        for i, row in enumerate(target['candidate_minima']):
            assert row['constellation'] == names[i]
            assert abs(float(scores[i].min())-row['score']) < 1e-12
            witness = row['witness']
            perm = permutations[witness['permutation_index']]
            X, Y = points[i], query[list(perm)]
            # Independent SVD witness on original, unnormalized coordinates.
            xc, yc = X-X.mean(axis=0), Y-Y.mean(axis=0)
            U, singular, Vh = np.linalg.svd(xc.T@yc)
            diagonal = np.array([1, witness['orientation']*np.sign(np.linalg.det(U@Vh))])
            rotation = (U*diagonal)@Vh
            scale = max(0, float(np.sum(singular*diagonal)/np.sum(xc*xc)))
            translation = Y.mean(axis=0)-X.mean(axis=0)@rotation*scale
            residual = X@rotation*scale+translation-Y
            assert np.allclose(residual, witness['residual_vectors'], atol=1e-9, rtol=0)
            assert abs(float(np.sqrt(np.mean(np.sum(residual*residual, axis=1))))-witness['rms_query_units']) < 1e-9
            for reference in references:
                expected = row['full_selection_references'][reference['generator']]
                count = sum(r['minimum'] <= row['score'] for r in reference['outcomes'])
                assert count == expected['count_at_or_below']
                assert expected['plus_one_fraction'] == (count+1)/4096
    reference_samples = 0
    for reference in references:
        assert len(reference['outcomes']) == reference['queries'] == 4095
        assert [r['ordinal'] for r in reference['outcomes']] == list(range(4095))
        for ordinal in [0, 1, 2, 3, 4091, 4092, 4093, 4094]:
            sample = reference['outcomes'][ordinal]
            scores = all_scores(points, sample['query_points'])
            assert abs(float(scores.min())-sample['minimum']) < 1e-12
            reference_samples += 1
    print(json.dumps({'independent_SVD_target_registration_scores': 63360,
                      'independent_SVD_target_witnesses': 264,
                      'maximum_normalized_score_delta': maximum_delta,
                      'full_reference_counts_rechecked': 528,
                      'full_search_reference_SVD_samples': reference_samples,
                      'reference_sample_registration_scores': reference_samples*21120,
                      'status': 'PASS'}))


if __name__ == '__main__':
    main()
