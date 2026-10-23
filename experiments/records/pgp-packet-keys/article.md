# Cicada's PGP key bytes as a repeating rune key

**The four tested public-key byte streams did not produce a complete English-like LP2 page under this simple rule.** Across 119,900 page, key-phase and sign settings, none reached the predeclared English score of −5.5. The best scored −6.456 on LP2-49. In 174 of 199 shuffled-page controls, the strongest result was at least as high. This is a newly defined bounded test of PGP key material, **not** a replay of a claimed historical decryption.

![The highest page score from each of four PGP packet or fingerprint key streams remains below the English gate.](experiments/records/pgp-packet-keys/scores.svg)

The four bars show each material's best *whole-page* score, after trying every starting phase and both arithmetic signs. All remain below the threshold. The 199 controls repeat the **entire search** after shuffling runes within each page, so their 174 comparable maxima include the effect of selecting a favorite key phase and page.

## The exact rule

We extracted the version-4 RSA **primary public-key packet** and **public subkey packet** from the [preserved Cicada key used in the RSA payload audit](#/experiments/public-rsa-payload-e01). Their 20-byte binary fingerprints are the other two candidates. The packet bodies are 525 bytes each; the fingerprints are 20 bytes each. The parser checks both fingerprints against the pinned key record. No third-party PGP keys, signatures or armor text were used as key material.

Each byte becomes one rune-key value by taking `byte mod 29`. For each of the four resulting streams, we tested every cyclic starting phase and both signs in `plaintext = (ciphertext ± key) mod 29`. The key repeats and restarts at the beginning of each page. We scored all runes on each of the 55 nonempty LP2-00–55 pages, including headings. LP2-50 has no runes. There is no skip rule, Atbash step or adaptive word choice.

Before evaluating LP2, all nine 66-rune archived reading controls scored above −5.5. Nine planted tests used those readings with fixed choices of key material, phase and sign; each recovered the reading exactly. A separate direct Latin-string quadgram implementation agreed with the accelerated scorer at fixed settings. This supports the scorer and decoder, but it cannot establish that the manuscript should use PGP key bytes at all.

| Result | Count |
| --- | ---: |
| Complete-page settings | 119,900 |
| Settings at or above the English gate | 0 |
| Shuffled full searches meeting or exceeding the observed best | 174 / 199 |

The [plan](experiments/records/pgp-packet-keys/plan.json) and [results](experiments/records/pgp-packet-keys/results.json) give the exact source hashes, page and key rules, each material's best setting, per-page maxima and all 199 control maxima. Install the [two Python dependencies](experiments/records/pgp-packet-keys/requirements.txt), then run `python experiments/records/pgp-packet-keys/run.py --check` and `python experiments/records/pgp-packet-keys/check.py` from the repository root. The checker parses the armored key independently, reconstructs the page streams, verifies all 119,900 scores and reruns every complete-search control. It also scores selected outputs directly as Latin quadgrams.

This result is limited to one lossy `byte mod 29` conversion and a repeating additive key. Packet fields could be parsed differently, used once rather than repeated, combined with another key or applied through a different cipher. None of those alternatives is tested here; the public key's ordinary cryptographic role is also separate from this proposed LP2 use.
