# Short-seed search with withheld text: fixed protocol

## Question and relationship to prior work

Can a bounded seed search identify a planted additive keystream from an exact plaintext prefix, and do prefix matches predict the withheld continuation? This is a known-plaintext control motivated by Dukotah/cicada3301 revision `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`. It is not an execution of that repository's code or a manuscript decryption attempt.

Earlier Liberpedia search-maximum controls used an English score to rank candidates. Here no language model, score threshold or ranking is used. A crib means an assumed exact sequence of rune indices at an exact position. All prefix-compatible seeds are retained, including ties. Knowing the plaintext prefix is a strong assumption, not a conclusion inferred from ciphertext statistics.

This protocol is frozen before computing candidate streams or matches. Source length and earlier controls are already known. It is project-level preregistration, not blinded or independently registered work.

## Source and planted ciphertexts

Use all 95 `output_index` values from `exports/readings/lp2-57.csv`, in CSV order. Hash the source file in the companion specification. This supplies known plaintext for synthetic controls; the encrypted inputs are newly constructed and are not LP2-57's original cipher.

Two generators use SHA-256 and SHA-512 respectively. For each digest, hash these bytes in order: ASCII `liberpedia-seed-control:v1:`, a four-byte unsigned big-endian seed, and a four-byte unsigned big-endian counter. Counter starts at zero. Visit digest bytes in stored order; discard bytes >=232, reduce remaining bytes modulo 29, and concatenate until 95 values are available. Truncate to exactly 95. No offsets, resets, separators, sign changes, skips or other transforms are allowed. Rejection removes modulo bias only under a uniform-byte model; this does not prove hash-stream independence or uniformity.

For each generator plant seeds 17, 4095 and 4096. Encrypt index-wise as c[i]=(p[i]+k[i]) mod 29. This yields six fixtures. The search dictionary is exactly integer seeds 0..4095 inclusive for each generator. Seed 4096 is deliberately outside it. Seed encoding remains unsigned 32-bit; a 4096-value dictionary is not the whole possible seed space.

## Prefix and continuation tests

For every fixture, search each of the two generators separately. Use prefix lengths 2, 4, 8, 16 and 32. Run two crib conditions: the correct source prefix; and an incorrect crib obtained by increasing the first plaintext index by one modulo 29, leaving all other prefix indices unchanged. There are 6 fixtures × 2 search generators × 5 lengths × 2 crib conditions = 120 result cells.

A candidate survives when its stream prefix equals (c[i]-assumed_p[i]) mod 29 at every crib position. Retain every surviving seed in ascending order. For each survivor decode all 95 ciphertext indices and retain the complete candidate sequence, exact whole-text equality, exact withheld-suffix equality, and the number of correct withheld indices. The suffix starts immediately after the crib. Whole-text equality and suffix equality must stay separate, especially for the incorrect crib. Do not select candidates using withheld text; it is only a post-search test with known ground truth.

Record whether the planted generator/seed pair belongs to the searched family and dictionary. A different pair might reproduce a finite stream, so distinguish generating-pair identity from exact plaintext recovery. Do not assume that the seed outside the dictionary or the other generator cannot accidentally match a finite prefix or full stream.

Retain the 95-index stream for every candidate seed under both search generators (8192 streams), all six planted ciphertexts and every result cell. Reused streams and plaintext make the cells dependent. Counts here are not estimates of population recovery probabilities.

## Verification and reporting

The producer checks the specification and source hashes. A checker that does not import producer code reconstructs digest input bytes, rejection conversion, every searched stream, planted ciphertext and prefix match; it independently decodes each survivor and checks the full and withheld comparisons. Include byte-boundary controls for 231/232/255 and counter/seed endianness. Small exhaustive modular fixtures should demonstrate that prefix agreement need not predict a suffix, and that an incorrect first crib rune necessarily prevents exact whole-text recovery.

Publish every cell, not only included-seed successes or the most striking false match. A figure should show surviving candidates as crib length grows, distinguishing matching-generator/included-seed, matching-generator/excluded-seed, wrong-generator and incorrect-crib conditions. These are controlled conditions, not candidate languages or evidence for a favored LP cipher. Explain any finite-stream collision rather than discarding it.

This bounds two declared generators and 4096 candidate seeds each under exact alignment. It cannot identify the manuscript generator, rule out all short-seed streams, establish a one-time pad, or infer any language. A successful planted control is necessary evidence that this search works under its assumptions; it is not evidence that those assumptions hold for LP.
