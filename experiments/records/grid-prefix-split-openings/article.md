## Result

**No suffix channel recovered any of nine fixed 12-rune openings at the start of an unsolved LP2 page.** The test covered every real key phase, both Vigenère signs, and all **55 nonempty pages LP2-00–55**: 58,190 named page configurations and 523,710 exact opening comparisons. The longest partial prefix was **three runes**. This checks one concrete way to use the channels as repeating keys; it does not exclude a later starting position or a different grid readout.

![The 256 grid tokens divide into five prefix channels; suffixes are mapped to rune keys and compared with fixed openings.](experiments/records/grid-prefix-split-openings/channels.svg)

## From grid cells to candidate keys

Each of the 256 two-character grid tokens has a leading digit `0`–`4`. Keeping the suffixes in printed sequence within each leading-digit class produces streams of **60, 58, 65, 56 and 17 symbols**. For each stream, we mapped each suffix to its base-60 digit value modulo 29 or to its ASCII byte value modulo 29. The `4` channel also has a direct hexadecimal-nibble reading, because all 17 suffixes are hex digits. Its exact string is `97DEF756B98A80EB9`.

Those **17 nibbles are not a whole number of bytes**. The test treats them as 17 numbers from 0 to 15, without padding or packing. That happens to give the same GP29 key values as their base-60 digit interpretation; the two named routes are reported, but the identical key was computed only once. There are 1,058 named mapping/phase/sign settings, of which 34 are this duplicate representation; each setting was checked against 55 page starts and nine openings.

For a key `K` and page ciphertext `C`, the test calculated `P[j] = C[j] ± K[(j + phase) mod length(K)] (mod 29)` for the first 12 runes. It used both signs and every phase from zero to the full key length minus one. The nine opening vectors were fixed from the archived known readings before the grid result was calculated. The same page-level rune selection includes headings and ignores layout marks. Planted encryptions with a 17-value key, a wrapped nonzero phase and both signs recovered their exact 12-rune text.

The [frozen plan](experiments/records/grid-prefix-split-openings/plan.json) pins the grid, page texts and opening traces by SHA-256. Run `python experiments/records/grid-prefix-split-openings/run.py` to regenerate the [group results](experiments/records/grid-prefix-split-openings/results.json), then `python experiments/records/grid-prefix-split-openings/check.py` for independent stream reconstruction and a full comparison recount.

The proposal also suggests treating the leading digits as directional route instructions. **No five-state direction table, origin or readout is specified**, so that different idea was not simulated here. Nor does this opening test examine later offsets, interruptions, nonrepeating keys or language scores.
