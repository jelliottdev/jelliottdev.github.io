# What do the unkeyed number-grid bytes tell us?

The [256-cell number grid](#/wiki/alphanumeric-grids) can be read as 256 bytes. Two parts of Wulfic's Stage X inspect those bytes directly: seven measurements against random blocks, and four readings as a possible RSA modulus. We reproduced all **eleven source rows exactly** and independently checked the measurements and divisibility tests.

**Finding:** none of the seven measurements crosses the source's threshold for rejecting its uniform-byte reference. But all four integer readings have small prime factors, including **3 and 7**. They therefore fail the proposed interpretation as a conventional RSA modulus formed from large primes. These are structural checks, not a decryption.

![The grid has 161 distinct byte values versus about 162 under the random reference; all four integer readings have small factors.](experiments/records/wulfic-grid-rsa-modulus-screen/byte-checks.svg)

## What the byte measurements establish

The source generated **100,000 independent, uniformly random 256-byte blocks**. It compared the printed grid with those blocks using seven fixed measurements and a two-sided cutoff of **0.01 / 7**, allowing for the seven comparisons.

| Measurement | Printed grid | Random-reference mean |
| --- | ---: | ---: |
| Different byte values | 161 | 162.00 |
| Byte-count chi-square | 254 | 254.97 |
| One bits among 2,048 bits | 1,017 | 1,023.98 |
| High-nibble chi-square | 14.625 | 14.98 |
| Low-nibble chi-square | 18.75 | 15.00 |
| Equal adjacent bytes, rows | 0 | 0.99 |
| Equal adjacent bytes, columns | 3 | 0.99 |

A nibble is half a byte: the high and low four-bit parts. The chi-square measurements compare how evenly values appear. None of these results rejects the declared reference. That **does not prove randomness**, encryption, compression, or a one-time pad. Many constructed messages can pass a small collection of statistical tests.

## Could the grid itself be an RSA modulus?

An RSA modulus is the public integer formed by multiplying prime factors; it is different from an RSA ciphertext or signature. The source tests printed row order and column order, each interpreted with the first byte most significant or least significant. It requires an odd, exactly 2,048-bit integer with no prime factor below one million.

| Reading | Bits | Examples of exact prime divisors |
| --- | ---: | --- |
| Rows, big-endian | 2,048 | 2, 3, 7, 13 |
| Rows, little-endian | 2,047 | 3, 7, 11 |
| Columns, big-endian | 2,048 | 2, 3, 7, 19 |
| Columns, little-endian | 2,047 | 3, 7, 13, 61 |

We tested all **78,498 primes below one million** against each integer. The [results](experiments/records/wulfic-grid-rsa-modulus-screen/results.json) retain every divisor found and the complete integers. A divisor such as 3 is an exact witness against a product made only from large primes; it is not a probabilistic primality result. This does not supply a full factorization, and it does not exclude arbitrary weak RSA parameters, another ordering, changed grid cells, or use of the bytes as ciphertext. [Applying public RSA keys to the payload](#/experiments/public-rsa-payload-e01) is a separate experiment.

## Reproduce

From the repository root, with Python and NumPy:

```text
python experiments/records/wulfic-grid-rsa-modulus-screen/run.py --check
python experiments/records/wulfic-grid-rsa-modulus-screen/check.py
python experiments/records/wulfic-grid-rsa-modulus-screen/plot.py --check
```

The producer reconstructs the grid from Liberpedia's tokens, uses vectorized count tables for the random reference, and exhausts the small-prime screen. The separate checker uses scalar counts and incremental prime generation. The [plan](experiments/records/wulfic-grid-rsa-modulus-screen/plan.json), [X1 scope amendment](experiments/records/wulfic-grid-rsa-modulus-screen/amendment.json), and [source rows](experiments/records/wulfic-grid-rsa-modulus-screen/source-x1-x3.tsv) preserve the exact bounds.

To repeat the original [Stage X1 and X3 code](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_x.py), use a checkout at that revision:

```text
python experiments/records/wulfic-grid-rsa-modulus-screen/replay_source.py PATH_TO_WULFIC_CLONE
```

The wrapper verifies that the source's grid parser and Liberpedia's export produce identical bytes, reruns these two components only, and compares all eleven rows with the committed source table. It writes no files into the external checkout.
