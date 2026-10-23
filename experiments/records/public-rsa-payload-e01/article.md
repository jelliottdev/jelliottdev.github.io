# The 256-byte grid payload as an RSA block

## Finding

The [published E-01 test](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round18/L5-payload/PREREG.md) interprets the **whole 256-byte payload from LP2 pages 49–51** as an RSA value. We reproduced its **162 structural checks** under Cicada's 4096-bit PGP primary key and subkey. **None** produced a PKCS#1 v1.5 signature frame, a PKCS#1 v1.5 encryption frame, or the tested PSS frame. The source's genuine-signature controls fired; 10,000 random control blocks produced no strict hits.

![The two 4096-bit PGP moduli each support 81 evaluated checks with zero structural hits. The 432-bit 2013 modulus supports none because the whole payload is larger than the modulus.](experiments/records/public-rsa-payload-e01/rsa-scope.svg)

The third modulus in the source grid, from the **2013 welcome message**, is only **432 bits**. Every whole-payload value is at least as large as it, so **zero** valid RSA inputs are evaluated under that modulus. The test also skips six left-aligned encodings that are too large for their 4096-bit modulus. Altogether it records **12 excluded encodings** before crossing valid inputs with three exponents and three structural checks.

## What was checked

The source specifies three pinned 256-byte payload readings: the majority transcription, decimal-preferred transcription, and its resolved reading. For each valid byte order and zero-extension convention it calculates `s^e mod n`, with public exponents **65537, 3, and 17**, and examines the resulting block for the specified padding structure. The full [source results](experiments/records/public-rsa-payload-e01/source-expected.json) and our [replay summary](experiments/records/public-rsa-payload-e01/results.json) agree on every evaluated row, not just the headline count. The 3 and 17 exponents are exploratory alternatives; the PGP keys themselves specify 65537.

This is a **public-power structure test**. If the payload were an RSA-encrypted ciphertext, applying the public exponent again would not decrypt it; decryption would require the private exponent. The null result covers these whole-payload representations under these two PGP moduli and structural predicates. It does not rule out an internal 54-byte RSA block, a private-key operation, a different encoding, or another role for the number grid. The separate [54-byte window test](#/experiments/rsa-window-54-source-replay) covers a different construction.

## Reproduce

The [plan](experiments/records/public-rsa-payload-e01/plan.json) pins the source revision, minimal source files, PGP armor, 2013 witness, payload bytes and historical output by SHA-256. The source is included under its MIT license. Run `python experiments/records/public-rsa-payload-e01/run.py --check` from the repository root to execute the original program in a temporary copy and compare its stable rows with the archived output. Run `python experiments/records/public-rsa-payload-e01/check.py` to independently extract the PGP modulus and fingerprint, verify the 2013 modulus, recompute all 162 public-power outputs, and check the padding predicates. The original source's planted controls require the `cryptography` Python package; the independent checker uses only Python's standard library.
