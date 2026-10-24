"""Small phone-readable diagram of the actual forward-map conflict."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def svg():
    result = json.loads((HERE/'target-results.json').read_text(encoding='utf8'))
    case = next(row for row in result['cases'] if row['encoding'] == 'IA_separate')
    assert result['cipher_indices'][1] == result['cipher_indices'][5] == 0
    assert case['labels'][1] == 'G' and case['labels'][5] == 'T'
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="280" height="328" viewBox="0 0 280 328" role="img" aria-labelledby="title desc">
<title id="title">The same ciphertext F would need two different letters</title>
<desc id="desc">In the fixed fourteen-rune slot, ciphertext positions two and six are both F, GP index zero. EGALITARIANISM would require G at position two and T at position six. A fixed substitution cannot assign both.</desc>
<rect width="280" height="328" fill="#fff"/>
<g font-family="Arial,sans-serif" fill="#263746">
<text x="16" y="29" font-size="18" font-weight="bold">Same rune. Different letters.</text>
<text x="16" y="57" font-size="15">LP2-43 · within the fixed word</text>
<text x="16" y="95" font-size="15">Position</text><text x="107" y="95" font-size="15">Cipher</text><text x="203" y="95" font-size="15">Crib</text>
<path d="M16 106H264" stroke="#cbd4dc"/>
<text x="39" y="145" font-size="22">2</text><text x="122" y="145" font-size="27" font-weight="bold" fill="#315c79">F</text><text x="211" y="145" font-size="27" font-weight="bold">G</text>
<path d="M153 137H190m-6-5 6 5-6 5" fill="none" stroke="#657989" stroke-width="2"/>
<rect x="16" y="168" width="248" height="61" fill="#f0f3f6"/>
<text x="39" y="207" font-size="22">6</text><text x="122" y="207" font-size="27" font-weight="bold" fill="#315c79">F</text><text x="211" y="207" font-size="27" font-weight="bold">T</text>
<path d="M153 199H190m-6-5 6 5-6 5" fill="none" stroke="#657989" stroke-width="2"/>
<text x="16" y="262" font-size="16">One fixed alphabet cannot do both.</text>
<text x="16" y="288" font-size="15">F is the cipher label, not plaintext.</text>
<text x="16" y="312" font-size="14">Positions count from 1 within the slot.</text>
</g></svg>
'''


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    path = HERE/'conflict.svg'
    if parser.parse_args().check:
        assert path.read_text(encoding='utf8') == svg()
    else:
        path.write_text(svg(), encoding='utf8', newline='\n')
    print('Conflict diagram checked against actual target positions 2 and 6.')
