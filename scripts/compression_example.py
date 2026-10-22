"""Two toy demonstrations: symbol packing and checking a zlib stream boundary."""
from pathlib import Path
import json
import zlib

ROOT = Path(__file__).resolve().parents[1]


def build():
    symbols = list(range(8))
    fields = [f'{x:05b}' for x in symbols]
    packed = int(''.join(fields), 2).to_bytes(5, 'big')
    value = 0
    for x in symbols:
        value = value * 29 + x
    radix_bytes = value.to_bytes((value.bit_length()+7)//8, 'big')
    assert packed.hex(' ') == '00 44 32 14 c7'
    assert radix_bytes.hex(' ') == '26 08 2a 9c'
    recovered = [int(f'{int.from_bytes(packed, "big"):040b}'[i:i+5], 2)
                 for i in range(0, 40, 5)]
    assert recovered == symbols

    # This independent fixture is NOT the packed symbols above.
    message = b'A complete toy message.'
    compressed = zlib.compress(message)
    cases = []
    for label, data in [('Complete stream', compressed),
                        ('Final byte removed', compressed[:-1]),
                        ('Five extra bytes', compressed+b'EXTRA')]:
        decoder = zlib.decompressobj()
        output = decoder.decompress(data, 4096)
        assert output == message and not decoder.unconsumed_tail
        cases.append(dict(name=label, input_hex=data.hex(), output=output.decode('ascii'),
                          eof=decoder.eof, unused_data_hex=decoder.unused_data.hex(),
                          unconsumed_tail_hex=decoder.unconsumed_tail.hex()))
    assert [case['eof'] for case in cases] == [True, False, True]
    assert [case['unused_data_hex'] for case in cases] == ['', '', b'EXTRA'.hex()]
    report = dict(scope='Independent invented examples; no manuscript inputs or format search.',
                  zlib_runtime=zlib.ZLIB_RUNTIME_VERSION,
                  packing=dict(symbols=symbols, five_bit_fields=fields,
                               packed_hex=packed.hex(' '), base29_value=value,
                               base29_minimal_bytes_hex=radix_bytes.hex(' ')),
                  decompression_cases=cases)
    (ROOT/'exports/compression-example.json').write_text(
        json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    print('Verified packing round trip and complete/truncated/trailing-data fixtures.')


if __name__ == '__main__':
    build()
