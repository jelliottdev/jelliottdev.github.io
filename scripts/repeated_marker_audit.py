"""Locate two specified repeated markers and audit declared gaps/alignment arithmetic."""
import argparse
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'exports/repeated-marker-audit.json'


def report():
    paths = ['data/index.json'] + [f'text/lp2-{n:02}.txt' for n in range(56)]
    blobs = {p: (ROOT / p).read_bytes() for p in paths}
    alphabet = json.loads(blobs[paths[0]])['alphabet']
    lookup = {a['rune']: (i, a) for i, a in enumerate(alphabet)}
    by_label = {a['latin']: a['rune'] for a in alphabet}
    streams = []
    cumulative = 0
    for path in paths[1:]:
        raw = blobs[path].decode('utf-8')
        unknown = {c for c in raw if '\u16a0' <= c <= '\u16ff'} - lookup.keys()
        if unknown:
            raise ValueError(f'Unknown runes: {unknown}')
        positions = [i for i, c in enumerate(raw) if c in lookup]
        text = ''.join(raw[i] for i in positions)
        streams.append(dict(page=Path(path).stem, text=text, positions=positions, global_start=cumulative))
        cumulative += len(text)
    def occurrences(labels):
        pattern = ''.join(by_label[x] for x in labels)
        hits = []
        for stream in streams:
            for start in range(len(stream['text']) - len(pattern) + 1):
                if stream['text'][start:start + len(pattern)] == pattern:
                    hits.append(dict(page=stream['page'], start_rune=start,
                                     end_rune_exclusive=start + len(pattern),
                                     global_start=stream['global_start'] + start,
                                     source_start=stream['positions'][start],
                                     source_end_inclusive=stream['positions'][start + len(pattern) - 1]))
        return hits
    d = occurrences(['D', 'J', 'U', 'B', 'E', 'I'])
    o = occurrences(['O', 'F', 'L', 'OE', 'NG'])
    assert len(d) == len(o) == 2
    gap = d[1]['global_start'] - d[0]['global_start']
    first_stream = next(s for s in streams if s['page'] == d[0]['page'])
    after = first_stream['text'][d[0]['end_rune_exclusive']]
    assert lookup[after][1]['latin'] == 'AE'
    aligned = []
    earlier, later = [next(s for s in streams if s['page'] == h['page']) for h in o]
    # Sixteen positions are the span supplied by the claim, not a searched length.
    for offset in range(16):
        left = lookup[earlier['text'][o[0]['start_rune'] + offset]]
        right = lookup[later['text'][o[1]['start_rune'] + offset]]
        index_difference = (right[0] - left[0]) % 29
        prime_difference = (right[1]['prime'] - left[1]['prime']) % 29
        aligned.append(dict(offset=offset, earlier_label=left[1]['latin'], later_label=right[1]['latin'],
                            earlier_index=left[0], later_index=right[0], earlier_prime=left[1]['prime'], later_prime=right[1]['prime'],
                            index_difference=index_difference, index_output=alphabet[index_difference]['latin'],
                            prime_difference=prime_difference, prime_residue_as_index=alphabet[prime_difference]['latin']))
    return dict(scope='Archived LP2-00–55 in order, alphabet runes only, headings retained; marker occurrences must be within one page. Global ordinals concatenate all pages, including empty rune streams. No corrections.',
                index_convention='All rune and character positions zero-based; marker ends exclusive. Source offsets are Unicode character offsets, not bytes.',
                input_sha256={p: hashlib.sha256(b).hexdigest() for p, b in blobs.items()},
                total_runes=cumulative, djubei=d, ofloeng=o,
                djubei_distances=dict(start_to_start=gap, strictly_between_six_rune_markers=gap-6,
                                      after_first_marker_and_following_AE=gap-7,
                                      note='6388 excludes the AE after the first marker; AE is not part of the identical six-rune marker.'),
                aligned_16_positions=aligned,
                limitation='Selected marker and output span from a proposal. Arithmetic reproduction only; no search-adjusted probability, plaintext validation or inferred cipher rule. Prime residues are shown with an explicitly chosen index interpretation, not silently equated with prime values.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = report()
    if args.check:
        assert result == json.loads(OUTPUT.read_text(encoding='utf-8'))
        print('PASS: marker locations, gap conventions and both subtraction representations')
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
