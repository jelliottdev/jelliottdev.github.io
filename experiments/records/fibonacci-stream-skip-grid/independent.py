"""Independent scalar conditional-skip decoder and separately parsed model."""
import math
from pathlib import Path
HERE=Path(__file__).resolve().parent

def independent_model():
    raw = {}
    for line in (HERE / 'source/liber-primus/data/english_quadgrams.txt').read_text(encoding='ascii').splitlines():
        word, count = line.split()
        raw[word] = int(count)
    total = sum(raw.values())
    return ({word: math.log10(count) - math.log10(total) for word, count in raw.items()}, math.log10(0.01) - math.log10(total))

MODEL,FLOOR=independent_model()

def score(text):
    return sum((MODEL.get(text[i:i + 4], FLOOR) for i in range(len(text) - 3))) / (len(text) - 3)

def decode(cipher, key, sign, offset, length, width, spellings):
    p0 = (cipher[0] + sign * key[offset]) % 29
    states = [(0.0, offset, (p0,), spellings[p0], (offset,))]
    for i in range(1, length):
        candidates = []
        for cumulative, pointer, plain, text, used in states:
            for skipped in range(4):
                position = pointer + 1 + skipped
                if position >= len(key):
                    break
                plain_value = (cipher[i] + sign * key[position]) % 29
                if any(((plain_value - sign * key[j]) % 29 != cipher[i - 1] for j in range(pointer + 1, position))):
                    continue
                extended = text + spellings[plain_value]
                delta = sum((MODEL.get(extended[end - 4:end], FLOOR) for end in range(max(4, len(text) + 1), len(extended) + 1)))
                candidates.append((cumulative + delta, position, plain + (plain_value,), extended, used + (position,)))
        if not candidates:
            break
        candidates.sort(key=lambda item: item[0], reverse=True)
        states = candidates[:width]
    winner = max(states, key=lambda item: item[0])
    return (list(winner[2]), winner[3], list(winner[4]))
