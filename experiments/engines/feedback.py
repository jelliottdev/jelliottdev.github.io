"""Small, explicit GP-29 feedback ciphers for bounded manuscript sweeps.

Symbols are zero-based indices of the canonical 29-rune alphabet. Each page
starts afresh. In word-reset mode only a literal hyphen or period in the
transcription resets the local position; newlines and slashes are layout.
"""

MODULUS = 29
MODES = ("ciphertext", "plaintext")


def page_symbols(raw_text, alphabet):
    """Return rune indices and per-rune segment-start indices.

    The second list records the first position after the most recent '-' or
    '.', permitting both continuous and word-reset decoding from one parse.
    """
    if len(alphabet) != MODULUS or len(set(alphabet)) != MODULUS:
        raise ValueError("Expected 29 distinct alphabet runes")
    lookup = {rune: index for index, rune in enumerate(alphabet)}
    symbols, starts = [], []
    start = 0
    for char in raw_text:
        if char in lookup:
            symbols.append(lookup[char])
            starts.append(start)
        elif char in "-.":
            start = len(symbols)
        elif "\u16a0" <= char <= "\u16ff":
            raise ValueError(f"Runic-block symbol missing from alphabet: {char!r}")
    return symbols, starts


def _validate(values, mode, lag, primer, starts):
    if mode not in MODES:
        raise ValueError(f"Unknown feedback mode {mode!r}")
    if not (1 <= lag <= 16 and 0 <= primer < MODULUS):
        raise ValueError("Lag must be 1..16 and primer 0..28")
    if len(starts) != len(values):
        raise ValueError("One segment start is needed for each rune")
    if any(not 0 <= value < MODULUS for value in values):
        raise ValueError("Rune indices must be in 0..28")
    if any(not 0 <= start <= index for index, start in enumerate(starts)):
        raise ValueError("Segment starts must point to current or earlier indices")


def decode(ciphertext, mode, lag, primer, starts=None):
    """P[i] = C[i] - K[i] mod 29, using the indicated feedback source."""
    if starts is None:
        starts = [0] * len(ciphertext)
    _validate(ciphertext, mode, lag, primer, starts)
    plain = []
    for i, value in enumerate(ciphertext):
        key = primer if i - starts[i] < lag else (ciphertext[i-lag] if mode == "ciphertext" else plain[i-lag])
        plain.append((value-key) % MODULUS)
    return plain


def encrypt(plaintext, mode, lag, primer, starts=None):
    """Inverse construction, used for planted recovery controls."""
    if starts is None:
        starts = [0] * len(plaintext)
    _validate(plaintext, mode, lag, primer, starts)
    cipher = []
    for i, value in enumerate(plaintext):
        key = primer if i - starts[i] < lag else (cipher[i-lag] if mode == "ciphertext" else plaintext[i-lag])
        cipher.append((value+key) % MODULUS)
    return cipher
