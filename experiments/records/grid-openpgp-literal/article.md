# Does the 256-byte grid form an OpenPGP literal packet?

The first grid byte in printed row order is `CB`. In OpenPGP, that byte can begin a **literal-data packet**. It is a suggestive one-byte match, but the complete packet has to parse. Across **16,384 fixed grid readings**, none is a complete literal-data packet.

![Of 16,384 byte readings, 4,096 begin with the literal-data tag but fail the complete-packet test; 12,288 do not begin with that tag](experiments/records/grid-openpgp-literal/packet-screen.svg)

The 4,096 readings with `CB` at the start all leave bytes after the packet length says the packet ends. The other 12,288 do not start with a literal-data tag. This reproduces a narrow structural check motivated by the public repository's OpenPGP test; it does not mean the grid cannot encode some other kind of data.

## What was counted

The 256 cells printed across LP2-49–51 were converted under the [specified conditional base-60 digit order](#/wiki/alphanumeric-grids). We used the same 16 complete row/column routes and 1,024 readings of ten disputed `I`/`L` stem cells as the direct-byte experiment. This experiment adds a different recognizer: a complete OpenPGP **new-format tag-11 literal-data packet at byte zero**. It checks definite and partial lengths, complete consumption of all 256 bytes, the literal format byte (`b`, `t`, or `u`), the filename-length field, and the timestamp's presence.

The script tests two constructed positive controls: a normal complete packet and a valid packet whose first 128 body bytes use partial-length encoding. A truncated partial packet is rejected. These controls matter because the baseline grid starts with `CB E7`; `E7` denotes a 128-byte partial segment, which cannot be interpreted correctly by looking at only the first two bytes.

| Outcome | Readings |
| --- | ---: |
| Does not start with literal-data tag | 12,288 |
| Starts with tag, then fails complete packet framing | 4,096 |
| Complete literal-data packet | **0** |

## Boundary of the finding

This test reads untransformed bytes at offset zero and requires **one packet occupying the entire 256-byte stream**. It does not test hidden packets at later offsets, added prefixes, different base/character readings, a sequence of multiple OpenPGP packets, encryption, or other data formats. A one-byte OpenPGP resemblance cannot establish a payload; a negative complete-packet result is not a verdict on every possible transform.

## Reproduce

Extract the experiment and reference-data ZIP files into one folder, then run:

```sh
python experiments/records/grid-openpgp-literal/run.py --check
python experiments/records/grid-openpgp-literal/check.py
```

The first script uses only Python's standard library, verifies the hashed grid and stem input files, reruns all 16,384 reads, and checks the saved [result table](experiments/records/grid-openpgp-literal/results.json). The independent check audits how many bytes the `CB` starts actually consume: they end at offsets 94 or 217, leaving the rest of the 256-byte stream. For the general text and file-header screen on the same readings, see the [direct-byte experiment](#/experiments/grid-direct-bytes).
