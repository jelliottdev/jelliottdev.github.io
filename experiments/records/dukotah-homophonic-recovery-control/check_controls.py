"""Independent saved-control checks; imports neither producer nor source solver."""
import collections
import hashlib
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def close(left, right):
    assert abs(left - right) < 1e-10, (left, right)


def training_letters():
    words = []
    for name in ('solved_plaintext.txt', 'words_expanded.txt', 'thematic.txt'):
        text = (HERE / 'source/liber-primus/data/keys' / name).read_text(encoding='utf-8')
        token = ''
        for character in text + ' ':
            if character in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz':
                token += character
            else:
                if len(token) >= 2 and not (len(token) > 6 and all(c in 'ABCDEFabcdef' for c in token)):
                    words.append(token.upper())
                token = ''
    return ''.join(words)


def model_for(letters, k, width):
    rank = {letter: n for n, letter in enumerate('ETAOINSHRDLCUMWFGYPBVKJXQZ')}
    classes = [min(k - 1, rank[letter] * k // 26) for letter in letters]
    classes *= max(1, 300000 // len(classes))
    counts = collections.Counter(tuple(classes[i:i + width]) for i in range(len(classes) - width + 1))
    denominator = len(classes) - width + 1 + 0.1 * k ** width

    def score(labels):
        grams = collections.Counter(tuple(labels[i:i + width]) for i in range(len(labels) - width + 1))
        return sum(amount * math.log10((counts[gram] + 0.1) / denominator)
                   for gram, amount in grams.items()) / (len(labels) - width + 1)

    return score, rank


def assignment(matrix):
    """Maximum-weight one-to-one class matching, Hungarian integer algorithm."""
    n = len(matrix)
    u, v, p, way = [0] * (n + 1), [0] * (n + 1), [0] * (n + 1), [0] * (n + 1)
    for row in range(1, n + 1):
        p[0], column = row, 0
        distances, used = [math.inf] * (n + 1), [False] * (n + 1)
        while True:
            used[column] = True
            current, delta, next_column = p[column], math.inf, 0
            for candidate in range(1, n + 1):
                if not used[candidate]:
                    cost = -matrix[current - 1][candidate - 1] - u[current] - v[candidate]
                    if cost < distances[candidate]:
                        distances[candidate], way[candidate] = cost, column
                    if distances[candidate] < delta:
                        delta, next_column = distances[candidate], candidate
            for candidate in range(n + 1):
                if used[candidate]:
                    u[p[candidate]] += delta
                    v[candidate] -= delta
                else:
                    distances[candidate] -= delta
            column = next_column
            if p[column] == 0:
                break
        while column:
            p[column], column = p[way[column]], way[column]
    result = [None] * n
    for column in range(1, n + 1):
        result[p[column] - 1] = column - 1
    return result


def main():
    report = json.loads((HERE / 'controls-results.json').read_bytes())
    assert sha((HERE / 'controls-plan-frozen.json').read_bytes()) == report['plan_sha256']
    letters = training_letters()
    assert len(letters) == report['training_letters']
    assert sha(letters.encode()) == report['training_letters_sha256']
    diagnostics = []
    for case in report['cases']:
        k, seed = case['spec']['k'], case['spec']['seed']
        cipher, truth, psi_true = case['cipher'], case['truth'], case['true_psi']
        assert len(cipher) == len(truth) == 12956
        assert len(psi_true) == 29 and set(psi_true) == set(range(k))
        assert [psi_true[c] for c in cipher] == truth
        width = 4 if k <= 6 else 3 if k <= 12 else 2
        assert case['order'] == width
        score, rank = model_for(letters, k, width)
        # Independently reconstruct the source's local-RNG planted homophones.
        plain = [min(k - 1, rank[c] * k // 26) for c in (letters * math.ceil(12956 / len(letters)))[:12956]]
        assert plain == truth
        frequency = collections.Counter(truth)
        allocation = [1] * k
        for _ in range(29 - k):
            chosen = max(range(k), key=lambda c: frequency[c] / allocation[c])
            allocation[chosen] += 1
        local = np.random.default_rng(seed)
        symbols = local.permutation(29).tolist()
        pools, offset = [], 0
        for amount in allocation:
            pools.append(symbols[offset:offset + amount])
            offset += amount
        generated, previous = [], -1
        for label in plain:
            options = pools[label]
            current = options[int(local.integers(0, len(options)))]
            if case['spec']['suppress'] > 0 and current == previous and len(options) > 1 and local.random() < case['spec']['suppress']:
                current = options[int(local.integers(0, len(options)))]
            generated.append(current)
            previous = current
        assert generated == cipher
        close(score(truth), case['oracle_score'])
        fit = case['fit']
        decoded = [fit['returned_psi'][c] for c in cipher]
        assert set(fit['returned_psi']) == set(range(k))
        close(score(decoded), fit['returned_score'])
        close(score(fit['best_evaluated_labels']), fit['best_evaluated_score'])
        confusion = [[0] * k for _ in range(k)]
        for left, right in zip(truth, decoded):
            confusion[left][right] += 1
        assert confusion == fit['confusion']
        close(sum(a == b for a, b in zip(truth, decoded)) / len(truth), fit['returned_raw_position_accuracy'])
        close(sum(max(row) for row in confusion) / len(truth), fit['source_rowmax_accuracy'])
        assert (decoded == truth) == fit['returned_decode_exact']
        close(sum(a == b for a, b in zip(psi_true, fit['returned_psi'])) / 29, fit['returned_rune_map_accuracy'])
        bijection = assignment(confusion)
        aligned = sum(confusion[i][bijection[i]] for i in range(k)) / len(truth)
        global_rng = np.random.default_rng(3301 + seed)
        global_rng.permutation(len(cipher))  # Source's one-shuffle contrast.
        cut = len(cipher) * 7 // 10
        held = [case['heldout']['psi'][c] for c in cipher[cut:]]
        close(score(held), case['heldout']['score'])
        null = []
        for expected in case['heldout']['shuffle_scores']:
            value = score([held[i] for i in global_rng.permutation(len(held))])
            close(value, expected)
            null.append(value)
        mean = sum(null) / len(null)
        sd = math.sqrt(sum((value - mean) ** 2 for value in null) / len(null))
        close((score(held) - mean) / sd, case['heldout']['z'])
        close(score([case['source_partc']['psi'][c] for c in cipher]), case['source_partc']['score'])
        close((case['source_partc']['score'] - case['source_partc']['control_mean']) / case['source_partc']['control_sd'], case['source_partc']['z'])
        assert case['source_partc']['strict_z_above_3'] == (case['source_partc']['z'] > 3)
        assert case['source_partc']['strict_above_control_max'] == (case['source_partc']['score'] > case['source_partc']['control_max'])
        matched_rng = np.random.default_rng(6600 + seed)
        for control in case['matched_budget_controls']:
            shuffled = np.array(cipher, dtype=np.int64)[matched_rng.permutation(len(cipher))]
            assert sha(shuffled.astype('<i8').tobytes()) == control['cipher_sha256']
            assert set(control['psi']) == set(range(k))
            close(score([control['psi'][c] for c in shuffled]), control['score'])
        assert sum(control['score'] >= fit['returned_score'] for control in case['matched_budget_controls']) == case['matched_null_at_or_above_fit']
        diagnostics.append({'seed': seed, 'k': k, 'raw_position_accuracy': fit['returned_raw_position_accuracy'],
                            'source_rowmax_accuracy': fit['source_rowmax_accuracy'],
                            'bijective_aligned_accuracy': aligned,
                            'rowmax_predicted_class_count': len({row.index(max(row)) for row in confusion}),
                            'returned_terminal_below_best_evaluated': fit['returned_score'] < fit['best_evaluated_score'],
                            'source_partc_gate_pass': case['source_partc']['strict_z_above_3'] and case['source_partc']['strict_above_control_max'],
                            'source_heldout_gate_pass': case['source_heldout_strict_z_above_3'],
                            'exact_recovery': fit['returned_decode_exact']})
    receipt = {'checker_sha256': sha(Path(__file__).read_bytes()),
               'results_sha256': sha((HERE / 'controls-results.json').read_bytes()),
               'verified': 'All planted streams, returned/full-trace scores, 1500 held-out shuffle scores, all24 equal-budget shuffled-fit witnesses, source Part-C observed scores and gate arithmetic.',
               'not_independently_verified': 'Source Part-C 24 one-restart null-fit witnesses and the one-shuffle fit were not retained; their optimization/null moments remain producer summaries.',
               'diagnostics': diagnostics}
    with (HERE / 'independent-check.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(receipt, handle, indent=2)
        handle.write('\n')
    print(json.dumps(receipt['diagnostics'], indent=2))


if __name__ == '__main__':
    main()
