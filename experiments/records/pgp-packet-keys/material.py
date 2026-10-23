"""Extract only Cicada's v4 primary/subkey packet bodies and fingerprints."""
import base64
import hashlib
import re


def materials(armor):
    section = re.search(rb"-----BEGIN PGP PUBLIC KEY BLOCK-----(.*?)-----END PGP PUBLIC KEY BLOCK-----", armor, re.S)
    if section is None:
        raise ValueError("No public key armor")
    lines = [line.strip() for line in section.group(1).splitlines()
             if line.strip() and not line.startswith(b"=") and b":" not in line]
    stream = base64.b64decode(b"".join(lines), validate=True)
    pos = 0
    found = []
    while pos < len(stream):
        flag = stream[pos]
        if not flag & 0x80:
            raise ValueError("Invalid OpenPGP packet header")
        pos += 1
        if flag & 0x40:
            tag = flag & 0x3f
            first = stream[pos]
            pos += 1
            if first < 192:
                length = first
            elif first < 224:
                length = ((first - 192) << 8) + stream[pos] + 192
                pos += 1
            elif first == 255:
                length = int.from_bytes(stream[pos:pos + 4], "big")
                pos += 4
            else:
                raise ValueError("Partial packet length excluded")
        else:
            tag = (flag >> 2) & 15
            form = flag & 3
            if form == 3:
                raise ValueError("Indeterminate packet length excluded")
            width = (1, 2, 4)[form]
            length = int.from_bytes(stream[pos:pos + width], "big")
            pos += width
        body = stream[pos:pos + length]
        if len(body) != length:
            raise ValueError("Truncated OpenPGP packet")
        pos += length
        if tag in (6, 14):
            if body[0] != 4 or body[5] not in (1, 2, 3):
                raise ValueError("Expected version-4 RSA public packet")
            fingerprint = hashlib.sha1(b"\x99" + len(body).to_bytes(2, "big") + body).digest()
            found.append(("primary" if tag == 6 else "subkey", body, fingerprint))
    if [row[0] for row in found] != ["primary", "subkey"]:
        raise ValueError("Expected one primary and one subkey")
    return found
