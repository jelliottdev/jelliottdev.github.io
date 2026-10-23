"""Strictly decode the frozen 168 LP2 rune-to-byte streams under five formats."""
import bz2
import hashlib
import importlib.util
import json
import lzma
import sys
import zlib
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / 'experiments/records/rune-direct-byte-packing/run.py'
CAP = 1_048_576
FORMATS = ('zlib', 'gzip', 'raw-deflate', 'bzip2', 'xz')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def decode(raw, fmt):
    """Return a separate status for invalid, incomplete, trailing and cap reached."""
    try:
        if fmt in ('zlib', 'gzip', 'raw-deflate'):
            wbits = {'zlib': 15, 'gzip': 31, 'raw-deflate': -15}[fmt]
            dec = zlib.decompressobj(wbits)
            out = dec.decompress(raw, CAP + 1)
            if len(out) > CAP:
                return {'status': 'output-limit'}
            if dec.unconsumed_tail:
                # With max_length > CAP, this can only be a capped expansion.
                return {'status': 'output-limit'}
            if not dec.eof:
                return {'status': 'incomplete'}
            if dec.unused_data:
                return {'status': 'trailing'}
            out += dec.flush(CAP + 1 - len(out))
        elif fmt in ('bzip2', 'xz'):
            dec = bz2.BZ2Decompressor() if fmt == 'bzip2' else lzma.LZMADecompressor(format=lzma.FORMAT_XZ)
            out = dec.decompress(raw, max_length=CAP + 1)
            if len(out) > CAP:
                return {'status': 'output-limit'}
            while not dec.eof and not dec.needs_input:
                more = dec.decompress(b'', max_length=CAP + 1 - len(out))
                out += more
                if len(out) > CAP:
                    return {'status': 'output-limit'}
            if not dec.eof:
                return {'status': 'incomplete'}
            if dec.unused_data:
                return {'status': 'trailing'}
        else:
            raise ValueError(fmt)
    except (zlib.error, OSError, EOFError, lzma.LZMAError):
        return {'status': 'invalid'}
    if len(out) > CAP:
        return {'status': 'output-limit'}
    return {'status': 'valid', 'output_bytes': len(out), 'output_sha256': sha(out)}


def compress(raw, fmt):
    if fmt == 'zlib':
        return zlib.compress(raw)
    if fmt == 'gzip':
        obj = zlib.compressobj(wbits=31)
        return obj.compress(raw) + obj.flush()
    if fmt == 'raw-deflate':
        obj = zlib.compressobj(wbits=-15)
        return obj.compress(raw) + obj.flush()
    if fmt == 'bzip2':
        return bz2.compress(raw)
    if fmt == 'xz':
        return lzma.compress(raw, format=lzma.FORMAT_XZ)
    raise ValueError(fmt)


def controls():
    message = b'liberpedia|strict-compression|control-v1\n'
    vector = []
    for fmt in FORMATS:
        raw = compress(message, fmt)
        good = decode(raw, fmt)
        short = decode(raw[:-1], fmt)
        junk = decode(raw + b'junk', fmt)
        bomb = decode(compress(b'Q' * (CAP + 1), fmt), fmt)
        assert good == {'status': 'valid', 'output_bytes': len(message), 'output_sha256': sha(message)}
        assert short['status'] == 'incomplete', (fmt, short)
        assert junk['status'] == 'trailing', (fmt, junk)
        assert bomb['status'] == 'output-limit', (fmt, bomb)
        vector.append({'format': fmt, 'valid': good, 'truncated': short['status'],
                       'trailing_junk': junk['status'], 'over_limit': bomb['status']})
    return vector


def rune_fivebit_fixture():
    """A complete zlib stream that can pass through the exact MSB five-bit packer."""
    compressed = zlib.compress(b'a0')
    bits = ''.join(f'{byte:08b}' for byte in compressed)
    assert len(bits) % 5 == 0
    indices = [int(bits[i:i+5], 2) for i in range(0, len(bits), 5)]
    assert len(indices) == 16 and max(indices) < 29
    repacked_bits = ''.join(f'{n:05b}' for n in indices)
    repacked = bytes(int(repacked_bits[i:i+8], 2) for i in range(0, len(repacked_bits), 8))
    assert repacked == compressed
    assert decode(repacked, 'zlib') == {'status': 'valid', 'output_bytes': 2,
                                        'output_sha256': sha(b'a0')}
    return {'format': 'zlib', 'rune_indices': indices, 'packed_hex': repacked.hex(),
            'output_bytes': 2, 'output_sha256': sha(b'a0')}


def streams():
    spec = importlib.util.spec_from_file_location('pinned_rune_direct_byte_packing', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pages, hashes = module.data()
    source_results = json.loads((SOURCE.parent / 'results.json').read_text(encoding='utf-8'))
    assert hashes == source_results['inputs_sha256']
    targets = {'all-lp2-00-55': [pair for pid in module.PAGES for pair in pages[pid]]}
    targets.update({pid: pairs for pid, pairs in pages.items() if pairs})
    assert len(targets) == source_results['targets'] == 56
    entries = []
    for target, pairs in targets.items():
        for mode in source_results['modes']:
            raw = module.encode(pairs, mode)
            entries.append((target, mode, len(pairs), raw))
    assert len(entries) == len(source_results['entries']) == 168
    for (target, mode, runes, raw), original in zip(entries, source_results['entries']):
        assert (target, mode, runes, len(raw), sha(raw)) == (
            original['target'], original['mode'], original['runes'], original['bytes'], original['sha256'])
    return entries


def build():
    plan_bytes = (HERE / 'plan.json').read_bytes()
    plan = json.loads(plan_bytes)
    assert plan['schema'] == 'liberpedia-rune-direct-compression-plan-v1'
    assert plan['formats'] == list(FORMATS)
    assert CAP == 1_048_576
    fixed_controls = controls()
    entries = []
    for target, mode, runes, raw in streams():
        for fmt in FORMATS:
            entries.append({'target': target, 'mode': mode, 'runes': runes,
                            'input_bytes': len(raw), 'input_sha256': sha(raw),
                            'format': fmt, **decode(raw, fmt)})
    by_format = {fmt: dict(sorted(Counter(e['status'] for e in entries if e['format'] == fmt).items()))
                 for fmt in FORMATS}
    return {'schema': 'liberpedia-rune-direct-compression-results-v1',
            'plan_sha256': sha(plan_bytes),
            'source_plan_sha256': sha((ROOT / plan['source_plan']).read_bytes()),
            'source_results_sha256': sha((ROOT / plan['source_results']).read_bytes()),
            'source_run_sha256': sha(SOURCE.read_bytes()),
            'input_stream_count': 168, 'format_count': 5, 'total_cases': len(entries),
            'output_limit_bytes': CAP, 'controls': fixed_controls,
            'rune_fivebit_fixture': rune_fivebit_fixture(),
            'by_format': by_format, 'entries': entries}


if __name__ == '__main__':
    result = build()
    encoded = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    if sys.argv[1:] == ['--write']:
        (HERE / 'results.json').write_bytes(encoded)
    elif not sys.argv[1:] or sys.argv[1:] == ['--check']:
        assert (HERE / 'results.json').read_bytes() == encoded
    else:
        raise SystemExit('usage: run.py [--write|--check]')
    print(f"{result['total_cases']} strict format tests; "
          f"{sum(v.get('valid', 0) for v in result['by_format'].values())} valid streams")
