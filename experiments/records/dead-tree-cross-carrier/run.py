"""Replay two bounded cross-carrier tree alignments; requires OpenCV and NumPy."""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FILES = {
    'lp2-55': ('images/lp2-55.jpg', 'a80191592add93a86ed3868f9e4e6ba3944ec20c9ffccc7d3e221b461344beba'),
    'lp2-32': ('images/lp2-32.jpg', 'c0f778187a8e9ddbfc667a65929ac567430a2e38278a2022377984ac084e5f72'),
    'commons': ('exports/sources/commons/DeadTree.jpg', '608288991f92b8ab901a9fbb39937f93ebdfeb5fd84edeecfa637d5262ff7b29'),
    'message-2016': ('images/message-2016.jpg', 'a8340ad04b83fb3130e7ed9172867a440812e87089d6aa2b932d97c6ae38aebe'),
}
CONFIG = {
    'manuscript': {
        'source': 'lp2-55', 'target': 'lp2-32',
        'source_crop': [600, 1450, 1800, 2500], 'target_crop': [550, 2000, 1850, 3500],
        'source_response': [250, 45, 'dark'], 'target_response': [230, 160, 'dark'],
        'source_mask_above': None, 'target_mask_above': None,
        'sigma': 15, 'scales': [round(.65 + i * .025, 3) for i in range(24)],
    },
    'message': {
        'source': 'commons', 'target': 'message-2016',
        'source_crop': [100, 500, 1750, 1950], 'target_crop': [145, 270, 425, 475],
        'source_response': [170, 130, 'dark'], 'target_response': [2, 28, 'light'],
        'source_mask_above': None, 'target_mask_above': 100,
        'sigma': 1.5, 'scales': [round(.065 + i * .003, 3) for i in range(26)],
    },
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(name):
    c = CONFIG[name]
    prepared = []
    for side in ('source', 'target'):
        path, expected = FILES[c[side]]
        file = ROOT / path
        assert sha(file) == expected, path
        image = cv2.imread(str(file), cv2.IMREAD_GRAYSCALE)
        x1, y1, x2, y2 = c[f'{side}_crop']
        assert 0 <= x1 < x2 <= image.shape[1] and 0 <= y1 < y2 <= image.shape[0]
        crop = image[y1:y2, x1:x2]
        level, span, direction = c[f'{side}_response']
        if direction == 'dark':
            response = np.clip((level - crop.astype(np.float32)) / span, 0, 1)
        else:
            response = np.clip((crop.astype(np.float32) - level) / span, 0, 1)
        ceiling = c[f'{side}_mask_above']
        if ceiling is not None:
            response[crop > ceiling] = 0
        prepared.append(response)
    source, target = prepared
    return source, cv2.GaussianBlur(target, (0, 0), c['sigma'])


def corr(a, b):
    x = a.ravel().astype(np.float64); y = b.ravel().astype(np.float64)
    x -= x.mean(); y -= y.mean()
    return float(np.dot(x, y) / np.sqrt(np.dot(x, x) * np.dot(y, y)))


def search(source, target, scales, sigma, flip, fraction):
    a = cv2.flip(source, 1) if flip else source
    best = None
    for scale in scales:
        t = cv2.GaussianBlur(cv2.resize(a, None, fx=scale, fy=scale), (0, 0), sigma)
        h, w = t.shape
        if h >= target.shape[0] or w >= target.shape[1]:
            continue
        training_height = h if fraction == 1 else int(h * fraction)
        scores = cv2.matchTemplate(target, t[:training_height], cv2.TM_CCOEFF_NORMED)
        if fraction < 1:
            scores[target.shape[0] - h + 1:] = -1
        _, score, _, (x, y) = cv2.minMaxLoc(scores)
        if best is None or score > best['training_correlation']:
            held = None if fraction == 1 else corr(t[training_height:], target[y + training_height:y + h, x:x + w])
            best = {'scale': scale, 'x': x, 'y': y, 'width': w, 'height': h,
                    'training_correlation': float(score), 'held_out_correlation': held}
    return best


def calculate():
    variants = {}
    for name, config in CONFIG.items():
        a, b = prepare(name)
        fits = {}
        for direction, reflected in [('same_orientation', False), ('horizontal_reflection', True)]:
            fits[direction] = {'full_region': search(a, b, config['scales'], config['sigma'], reflected, 1),
                               'top_fit_bottom_check': search(a, b, config['scales'], config['sigma'], reflected, .6)}
        variants[name] = {'source': {'path': FILES[config['source']][0], 'sha256': FILES[config['source']][1]},
                          'target': {'path': FILES[config['target']][0], 'sha256': FILES[config['target']][1]},
                          'settings': {k: v for k, v in config.items() if k not in ('source', 'target')},
                          'orientations': fits}
    return {'schema': 'liberpedia-cross-carrier-tree-v1', 'variants': variants,
            'interpretation': 'Exploratory, visually selected source images/crops/responses; descriptive correlations only. Upper 60% chooses transform and lower 40% checks it within each selected image, not in a blind independent test. No exact processing recipe or chance probability is inferred.'}


def render_variant(name, result, path):
    c = CONFIG[name]
    a, b = prepare(name)
    choice = 'same_orientation' if name == 'manuscript' else 'horizontal_reflection'
    fit = result['variants'][name]['orientations'][choice]['top_fit_bottom_check']
    oriented = a if choice == 'same_orientation' else cv2.flip(a, 1)
    t = cv2.GaussianBlur(cv2.resize(oriented, None, fx=fit['scale'], fy=fit['scale']), (0, 0), c['sigma'])
    x, y, w, h = (fit[k] for k in ('x', 'y', 'width', 'height'))
    aligned = np.zeros_like(b)
    aligned[y:y + h, x:x + w] = t
    width = 450
    panels = []
    for values in (aligned, b, .5 * aligned + .5 * b):
        pixels = np.uint8(255 - 215 * np.clip(values, 0, 1))
        panels.append(cv2.resize(pixels, (width, round(pixels.shape[0] * width / pixels.shape[1]))))
    height = panels[0].shape[0]
    canvas = np.full((height + 80, width * 3 + 60, 3), 245, np.uint8)
    labels = ('ALIGNED SOURCE', 'TARGET TREE', '50% OVERLAY')
    for i, panel in enumerate(panels):
        left = 15 + i * (width + 15)
        canvas[65:65 + height, left:left + width] = cv2.cvtColor(panel, cv2.COLOR_GRAY2BGR)
        cv2.putText(canvas, labels[i], (left, 37), cv2.FONT_HERSHEY_SIMPLEX, .65, (35, 45, 55), 2, cv2.LINE_AA)
    path.parent.mkdir(parents=True, exist_ok=True)
    assert cv2.imwrite(str(path), canvas)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true')
    p.add_argument('--output', type=Path)
    p.add_argument('--render-directory', type=Path)
    args = p.parse_args()
    result = calculate()
    if args.check:
        saved = json.loads((ROOT / 'exports/dead-tree-cross-carrier.json').read_text(encoding='utf-8'))
        for name in CONFIG:
            actual = result['variants'][name]
            expected = saved['variants'][name]
            assert actual['source'] == expected['source'] and actual['target'] == expected['target']
            assert actual['settings'] == expected['settings']
            for direction in actual['orientations']:
                for mode in actual['orientations'][direction]:
                    got = actual['orientations'][direction][mode]
                    want = expected['orientations'][direction][mode]
                    assert all(got[k] == want[k] for k in ('scale', 'x', 'y', 'width', 'height'))
                    for k in ('training_correlation', 'held_out_correlation'):
                        if got[k] is not None:
                            assert abs(got[k] - want[k]) < 1e-5
            preferred = 'same_orientation' if name == 'manuscript' else 'horizontal_reflection'
            alternative = 'horizontal_reflection' if name == 'manuscript' else 'same_orientation'
            assert actual['orientations'][preferred]['top_fit_bottom_check']['held_out_correlation'] > actual['orientations'][alternative]['top_fit_bottom_check']['held_out_correlation']
        print('PASS: four original hashes, both directions, bounded fits and lower-region checks')
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    if args.render_directory:
        for name in CONFIG:
            render_variant(name, result, args.render_directory / f'dead-tree-{name}.png')
    if not (args.check or args.output or args.render_directory):
        print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
