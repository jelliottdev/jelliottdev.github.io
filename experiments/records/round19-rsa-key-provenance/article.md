# A broader RSA scan, and what its keys actually are

## Finding

The pinned [Round 19 C1 E-01 source](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round19/C1/e01_rsa.py) tries the whole 256-byte LP2-49–51 number-grid payload under **23 named RSA moduli**. We reproduced all **738 named settings**: 594 valid public-power calculations, 144 inputs too large for their modulus, and **zero** of the specified PKCS#1 or PSS structural matches. The source's preserved control receipt records six successful genuine-frame plants and zero hits in its 10,000-block random gate. That random gate is a sample, not proof that its detector has zero false positives.

![The source's 738 RSA settings divided by key provenance and fit. Of 72 settings under the two Cicada PGP packets, 54 are evaluated and 18 excluded; 648 settings use 20 other archived PGP packets, with 540 evaluated and 108 excluded; 18 settings under the small 2013 puzzle modulus are all excluded.](experiments/records/round19-rsa-key-provenance/key-provenance.svg)

The key provenance changes how to read that result. The source's broad file scan found **22 PGP key packets**, but only **two** are the Cicada PGP primary key and subkey used in the [earlier whole-payload test](#/experiments/public-rsa-payload-e01). The other 20 are from files the repository holds for unrelated purposes: Bitcoin Core, Tails, Tor Browser, GnuPG, other solver material, and a separate keyserver witness. A key's presence somewhere in a Cicada research repository does not make it a key published by Cicada. The 2013 puzzle modulus is a separate 23rd candidate and is too small for the whole payload.

Thus the source arithmetic is reproducible, but its description of the extended scan as covering **23 published 3301 moduli** is unsupported by the witness files. The **540 valid rows under unrelated keys are exploratory comparisons**, not increased coverage of authenticated Cicada keys. The 54 valid Cicada-key settings correspond to the earlier record's 162 matcher checks (three matcher types per setting). We do not count them as a second independent failed idea.

## How the audit works

We pinned the three 256-byte payload readings, source script and output, original three-modulus list, and one armored witness containing each of the 22 PGP packets. The source's one missing vendor witness was fetched from its [public repository](https://github.com/aadishgoel/Cicada-3301/blob/master/PGPKey.txt); its three parsed fingerprints match the archived result. Each OpenPGP packet's v4 fingerprint and RSA modulus are derived from the packet bytes rather than accepted from a filename. The 738 settings retain source byte order, alignment, public exponents, and the source's PKCS#1 v1.5 type-1/type-2 and PSS checks.

The source's type-2 detector accepts a valid-looking `00 02 ... 00` frame without knowing a message to recover. A rare random match is therefore possible. Its historical 10,000-block gate passed, but the zero-match requirement can flip between runs; it should not be treated as a proven zero-false-positive instrument. The absence of structural hits in these 594 deterministic outputs remains reproducible.

There is no evidence here that the grid is an RSA ciphertext or signature. Public exponentiation also cannot decrypt a ciphertext without a private exponent. This record only tests the specified **whole-payload public-power interpretations**; it does not test 54-byte windows, unknown keys, private-key operations, or other padding and payload transforms.

## Reproduce

The [plan](experiments/records/round19-rsa-key-provenance/plan.json) pins every local input by SHA-256. Run `python experiments/records/round19-rsa-key-provenance/run.py --check` to reconstruct all source rows from the pinned packet moduli and payload bytes. Run `python experiments/records/round19-rsa-key-provenance/check.py` for an independent packet parser and arithmetic/structure check. To rerun the source's planted and random controls (requires `cryptography`), run `python -c "import sys; sys.path.insert(0, 'experiments/records/round19-rsa-key-provenance/source'); import e01_rsa; print(e01_rsa.positive_control())"` from the repository root. The random count can change between runs; it does not affect the deterministic arithmetic replay.
