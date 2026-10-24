"""Fixed window-balance and frequency-drift measurements; no file access or RNG."""
import numpy as np
from numba import njit

ALPHABET = 29
WIDTHS = (29, 58, 116, 232, 464)
METRICS = tuple(f'window_dispersion_{w}' for w in WIDTHS) + (
    'frequency_drift_4_bins', 'frequency_drift_8_bins', 'linear_drift_8_bins')
TAILS = ('lower',) * 5 + ('upper',) * 3


@njit(cache=True)
def window_square_sums(stream, widths):
    """Exact integer sum of histogram squares over every complete window."""
    totals = np.zeros(len(widths), dtype=np.int64)
    for j in range(len(widths)):
        width = widths[j]
        counts = np.zeros(29, dtype=np.int64)
        for i in range(width):
            counts[stream[i]] += 1
        square_sum = np.int64(0)
        for count in counts:
            square_sum += count * count
        total = square_sum
        for i in range(width, len(stream)):
            old = stream[i - width]
            new = stream[i]
            square_sum += -2 * counts[old] + 1
            counts[old] -= 1
            square_sum += 2 * counts[new] + 1
            counts[new] += 1
            total += square_sum
        totals[j] = total
    return totals


def table_for(stream, bins):
    # Floor(N*j/bins) cuts retain all symbols; no end padding or dropped tail.
    cuts = np.arange(bins + 1, dtype=np.int64) * len(stream) // bins
    table = np.array([np.bincount(stream[a:b], minlength=ALPHABET)
                      for a, b in zip(cuts[:-1], cuts[1:])], dtype=np.int64)
    return cuts, table


def drift_from_table(cuts, table):
    sizes = np.diff(cuts).astype(np.float64)
    probabilities = table.sum(axis=0) / sizes.sum()
    present = probabilities > 0
    expected = sizes[:, None] * probabilities[None, present]
    pearson = float(np.sum((table[:, present] - expected) ** 2 / expected))
    # Centers are positions of actual symbols, not simply equal bin ordinals.
    centers = (cuts[:-1] + cuts[1:] - 1) / 2.0
    weights = centers - np.dot(sizes, centers) / sizes.sum()
    weighted_counts = weights @ table[:, present]
    denominator = probabilities[present] * np.dot(sizes, weights * weights)
    linear = float(np.sum(weighted_counts * weighted_counts / denominator))
    return pearson, linear


def score_provenance(stream):
    """Eight fixed metrics; significance is calibrated by the caller's controls."""
    stream = np.asarray(stream)
    if (stream.ndim != 1 or len(stream) < max(WIDTHS)
            or not np.issubdtype(stream.dtype, np.integer)
            or np.any(stream < 0) or np.any(stream >= ALPHABET)):
        raise ValueError('Expected at least 464 integer rune indices in 0..28')
    stream = np.ascontiguousarray(stream, dtype=np.int64)
    totals = window_square_sums(stream, np.array(WIDTHS, dtype=np.int64))
    values = [ALPHABET * int(total) / (width * (len(stream) - width + 1)) - width
              for width, total in zip(WIDTHS, totals)]
    _, table4 = table_for(stream, 4)
    cuts4 = np.arange(5, dtype=np.int64) * len(stream) // 4
    cuts8, table8 = table_for(stream, 8)
    pearson4, _ = drift_from_table(cuts4, table4)
    pearson8, linear8 = drift_from_table(cuts8, table8)
    values.extend((pearson4, pearson8, linear8))
    return dict(zip(METRICS, map(float, values)))
