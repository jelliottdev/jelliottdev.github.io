"""Compare the mirrored Commons tree photograph with the LP2-55 tree region.

Requires OpenCV and NumPy. Parameters are frozen in plan.txt. This compares
image structure; it is not a reconstruction of the compositing recipe.
"""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'exports/sources/commons/DeadTree.jpg'
TARGET = ROOT / 'images/lp2-55.jpg'
EXPECTED_SOURCE = '608288991f92b8ab901a9fbb39937f93ebdfeb5fd84edeecfa637d5262ff7b29'
EXPECTED_TARGET = 'a80191592add93a86ed3868f9e4e6ba3944ec20c9ffccc7d3e221b461344beba'
SCALES = [round(.37 + i * .015, 3) for i in range(23)]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepared():
    assert digest(SOURCE) == EXPECTED_SOURCE
    assert digest(TARGET) == EXPECTED_TARGET
    source = cv2.imread(str(SOURCE), cv2.IMREAD_GRAYSCALE)
    target = cv2.imread(str(TARGET), cv2.IMREAD_GRAYSCALE)
    assert source.shape == (2606, 1894) and target.shape == (3600, 2400)
    source = source[500:1950, 100:1750]
    target = target[1300:2550, 550:1850]
    a = np.clip((170 - source.astype(np.float32)) / 130, 0, 1)
    b = np.clip((250 - target.astype(np.float32)) / 45, 0, 1)
    return a, cv2.GaussianBlur(b, (0, 0), 7)


def correlation(a, b):
    x = a.ravel().astype(np.float64)
    y = b.ravel().astype(np.float64)
    x -= x.mean(); y -= y.mean()
    return float(np.dot(x, y) / np.sqrt(np.dot(x, x) * np.dot(y, y)))


def search(source, target, flip, training_fraction):
    a = cv2.flip(source, 1) if flip else source
    best = None
    for scale in SCALES:
        template = cv2.GaussianBlur(cv2.resize(a, None, fx=scale, fy=scale), (0, 0), 7)
        h, w = template.shape
        if h >= target.shape[0] or w >= target.shape[1]:
            continue
        train_h = h if training_fraction == 1 else int(h * training_fraction)
        scores = cv2.matchTemplate(target, template[:train_h], cv2.TM_CCOEFF_NORMED)
        if training_fraction != 1:
            scores[target.shape[0] - h + 1:] = -1
        _, score, _, (x, y) = cv2.minMaxLoc(scores)
        if best is None or score > best['training_correlation']:
            held = None
            if training_fraction != 1:
                held = correlation(template[train_h:], target[y + train_h:y + h, x:x + w])
            best = dict(scale=scale, x=x, y=y, width=w, height=h,
                        training_correlation=float(score), held_out_correlation=held)
    return best


def calculate():
    a, b = prepared()
    return {
        'schema': 'liberpedia-tree-alignment-v1',
        'source': {'path': SOURCE.relative_to(ROOT).as_posix(), 'sha256': EXPECTED_SOURCE,
                   'original_size': [1894, 2606], 'crop_xyxy': [100, 500, 1750, 1950]},
        'target': {'path': TARGET.relative_to(ROOT).as_posix(), 'sha256': EXPECTED_TARGET,
                   'original_size': [2400, 3600], 'crop_xyxy': [550, 1300, 1850, 2550]},
        'preprocessing': 'grayscale; source response clip((170-L)/130,0,1); target response clip((250-L)/45,0,1); Gaussian sigma 7 after resizing',
        'search': {'scales': SCALES, 'translation': 'all in-crop integer offsets retaining the entire template',
                   'score': 'OpenCV TM_CCOEFF_NORMED; top 60% used for the held-out fit'},
        'orientations': {
            name: {'full_region': search(a, b, flip, 1), 'top_fit_bottom_check': search(a, b, flip, .6)}
            for name, flip in [('original', False), ('horizontal_reflection', True)]},
        'limits': 'Crops, darkness responses, scale interval and Gaussian width were chosen after inspecting these images. The lower 40% was not used to choose alignment within this declared run, but the overall design is exploratory. Correlations are descriptive, not a significance probability or exact compositing recipe.'
    }


def render(result, path):
    a, b = prepared()
    fit = result['orientations']['horizontal_reflection']['top_fit_bottom_check']
    template = cv2.GaussianBlur(cv2.resize(cv2.flip(a, 1), None, fx=fit['scale'], fy=fit['scale']), (0, 0), 7)
    x, y, w, h = (fit[k] for k in ('x', 'y', 'width', 'height'))
    target = np.uint8(255 - 215 * b)
    aligned = np.full_like(target, 255)
    aligned[y:y + h, x:x + w] = np.uint8(255 - 215 * template)
    blend = cv2.addWeighted(target, .5, aligned, .5, 0)
    # Each pane uses the same target-crop pixel coordinates; the first is the
    # reflected source at the fitted scale, with white where it has no data.
    scale = .48
    panes = [cv2.resize(z, None, fx=scale, fy=scale) for z in (aligned, target, blend)]
    canvas = np.full((panes[0].shape[0] + 80, panes[0].shape[1] * 3 + 60, 3), 245, np.uint8)
    labels = ('MIRRORED SOURCE / FIT', 'LP2-55 / GRAY TREE', '50% OVERLAY')
    for i, pane in enumerate(panes):
        left = 15 + i * (pane.shape[1] + 15)
        canvas[65:65 + pane.shape[0], left:left + pane.shape[1]] = cv2.cvtColor(pane, cv2.COLOR_GRAY2BGR)
        cv2.putText(canvas, labels[i], (left, 37), cv2.FONT_HERSHEY_SIMPLEX, .65, (35, 45, 55), 2, cv2.LINE_AA)
    path.parent.mkdir(parents=True, exist_ok=True)
    assert cv2.imwrite(str(path), canvas)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--render', type=Path)
    args = parser.parse_args()
    result = calculate()
    if args.check:
        saved = json.loads((ROOT / 'exports/dead-tree-alignment.json').read_text(encoding='utf-8'))
        assert result['source'] == saved['source'] and result['target'] == saved['target']
        for orientation in result['orientations']:
            for mode in result['orientations'][orientation]:
                got = result['orientations'][orientation][mode]
                expected = saved['orientations'][orientation][mode]
                assert all(got[k] == expected[k] for k in ('scale', 'x', 'y', 'width', 'height'))
                for k in ('training_correlation', 'held_out_correlation'):
                    if got[k] is not None:
                        assert abs(got[k] - expected[k]) < 1e-5
        reflected = result['orientations']['horizontal_reflection']['top_fit_bottom_check']
        original = result['orientations']['original']['top_fit_bottom_check']
        assert reflected['held_out_correlation'] > original['held_out_correlation']
        print('PASS: source hashes, both orientations, frozen search, and lower-region check')
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    if args.render:
        render(result, args.render)
    if not (args.check or args.output or args.render):
        print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
