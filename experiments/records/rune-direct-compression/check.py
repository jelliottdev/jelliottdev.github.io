"""Independent page-JSON byte construction and direct decompressor audit."""
import bz2
import hashlib
import json
import lzma
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FORMATS = ('zlib', 'gzip', 'raw-deflate', 'bzip2', 'xz')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def repack(pairs, mode):
    if mode == 'prime-byte':
        return bytes(prime for _, prime in pairs)
    digits = []
    for index, _ in pairs:
        if mode == 'index-5-lsb':
            index = sum(((index >> bit) & 1) << (4-bit) for bit in range(5))
        else:
            assert mode == 'index-5-msb'
        digits.append(index)
    accumulator = 0
    for digit in digits:
        accumulator = (accumulator << 5) | digit
    nbits = len(digits) * 5
    padded = (nbits + 7) // 8 * 8
    return (accumulator << (padded-nbits)).to_bytes(padded // 8, 'big')


def strict_probe(raw, fmt):
    """Second implementation, testing complete consumption with library EOF flags."""
    try:
        if fmt in ('zlib', 'gzip', 'raw-deflate'):
            decoder = zlib.decompressobj({'zlib': 15, 'gzip': 31, 'raw-deflate': -15}[fmt])
            output = decoder.decompress(raw, 1_048_577)
            if len(output) > 1_048_576 or decoder.unconsumed_tail:
                return 'output-limit'
            if not decoder.eof:
                return 'incomplete'
            if decoder.unused_data:
                return 'trailing'
            output += decoder.flush(1_048_577-len(output))
        else:
            decoder = bz2.BZ2Decompressor() if fmt == 'bzip2' else lzma.LZMADecompressor(format=lzma.FORMAT_XZ)
            output = decoder.decompress(raw, max_length=1_048_577)
            while not decoder.eof and not decoder.needs_input and len(output) <= 1_048_576:
                output += decoder.decompress(b'', max_length=1_048_577-len(output))
            if len(output) > 1_048_576:
                return 'output-limit'
            if not decoder.eof:
                return 'incomplete'
            if decoder.unused_data:
                return 'trailing'
        return ('valid', len(output), sha(output))
    except (zlib.error, OSError, EOFError, lzma.LZMAError):
        return 'invalid'


def main():
    result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    source = json.loads((ROOT / 'experiments/records/rune-direct-byte-packing/results.json').read_text(encoding='utf-8'))
    index = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))
    lookup = {item['rune']: (item['index'], item['prime']) for item in index['alphabet']}
    pages = {}
    for n in range(56):
        label = f'lp2-{n:02}'
        data = json.loads((ROOT / f'data/pages/{label}.json').read_text(encoding='utf-8'))
        raw = data['raw']
        text = (ROOT / f'text/{label}.txt').read_text(encoding='utf-8')
        assert tuple(c for c in raw if c in lookup) == tuple(c for c in text if c in lookup)
        pages[label] = [lookup[c] for c in raw if c in lookup]
        assert len(pages[label]) == data['rune_count']
    targets = {'all-lp2-00-55': [pair for n in range(56) for pair in pages[f'lp2-{n:02}']]}
    targets.update({pid: pairs for pid, pairs in pages.items() if pairs})
    assert len(targets) == result['input_stream_count'] // 3 == 56
    rebuilt = []
    for target, runes in targets.items():
        for mode in source['modes']:
            raw = repack(runes, mode)
            rebuilt.append((target, mode, raw))
    assert len(rebuilt) == len(source['entries']) == 168
    for (target, mode, raw), prior in zip(rebuilt, source['entries']):
        assert (target, mode, len(raw), sha(raw)) == (prior['target'], prior['mode'], prior['bytes'], prior['sha256'])
    assert len(result['entries']) == 840
    for i, (_, _, raw) in enumerate(rebuilt):
        for j, fmt in enumerate(FORMATS):
            entry = result['entries'][i*5+j]
            assert entry['format'] == fmt and entry['input_sha256'] == sha(raw)
            verdict = strict_probe(raw, fmt)
            assert entry['status'] == verdict == 'invalid', (entry['target'], entry['mode'], fmt, verdict)
    assert all(counts == {'invalid': 168} for counts in result['by_format'].values())

    # A truly compressed stream that survives one of the exact five-bit rune packings.
    fixture = result['rune_fivebit_fixture']
    packed = repack([(idx, 2) for idx in fixture['rune_indices']], 'index-5-msb')
    assert packed.hex() == fixture['packed_hex']
    assert strict_probe(packed, 'zlib') == ('valid', fixture['output_bytes'], fixture['output_sha256'])
    assert fixture['output_sha256'] == sha(b'a0')
    print('PASS: independent page-JSON construction, 168 stream hashes, 840 decoder statuses and rune-packed zlib control')


if __name__ == '__main__':
    main()
