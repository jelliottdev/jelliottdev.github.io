# Can selected F runes rescue these fixed keyword decodes?

The [archived second-layer program](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/p21_30_second_layer.py) proposes one keyword and arithmetic direction for each of ten page files. For every ciphertext F rune, it tries two possibilities: decrypt it normally, or output a literal F and **pause key advancement**. The committed files `page_21`–`page_30` match current **LP2-04–13** rune for rune.

## Result

Across the ten pages, the program's bounds allow **27,402 F masks**. **None** makes every one-rune word an I or A under the program's own separator rule. The unmodified source consequently takes its fallback branch and chooses a mask by index of coincidence (IoC) on every page. That fallback is a frequency ranking, not a successful one-rune-word check.

![The best-IoC F mask raises concentration on some pages, while zero of 27,402 masks passes the required word gate.](experiments/records/wulfic-p21-literal-f-masks/comparison.svg)

The source's next stage tries **45 fixed rune routes per page** on the *ordinary no-mask* decode. None crosses its printing gates. It also prints prime-word, reversed-word and first-25-word magic-square views, but does not score those word orders. Reordering whole words cannot change how many individual words match a dictionary.

We repeated the full mask selection on 19 seeded rune-order shuffles of all ten pages, keeping each page's rune inventory and visible word slots. **All 19 also produced zero pages with an all-singleton-valid mask.** That comparison shows this strict gate has little ability to distinguish the actual pages under this control; it does not provide evidence for or against other F-skip rules.

## What was checked

Before using the manuscript, a planted 20-rune message with **two literal-F pauses** was recovered exactly and passed both one-rune-word checks. The source functions and a separate scalar recurrence agreed on 48 small mask/mode cases, and the compiled all-mask selector agreed on the plant. We then ran the unmodified source script against the exact committed page bytes. Its ten fallback choices match the saved scan. An independent scalar checker enumerates every manuscript mask again and reconstructs the first complete shuffled search.

The source's keyword parser is part of this result. It turns `DEOR` into three GP runes because `EO` is a digraph; it silently drops the `V` in `DIVINITY`, despite a comment that suggests `V` should map to `U`. We preserved that actual behavior. A corrected parser or a different keyword would be a new test. The source only treats period, hyphen, bullet, space and newline as word separators, so its singleton positions can differ from other transcriptions.

## Reproduce and limits

The downloaded experiment contains everything needed for `python check.py` and `python plot.py`: run those commands from the extracted directory containing the scripts. To repeat the original-source parity check and full search, clone Wulfic at commit `bf89d3d` and run `python gate.py --source-root ABSOLUTE_CLONE_PATH --check` and `python run.py --source-root ABSOLUTE_CLONE_PATH --check` from the same directory. `snapshot_inputs.py --source-root ABSOLUTE_CLONE_PATH --check` additionally compares the source pages with Liberpedia's `data/pages` files, so run that check in a full Liberpedia checkout. The packaged input snapshot already records the exact Git-object hashes and page text.

This is one grouped replay of the source's **fixed ten keyword assignments and finite F-mask search**. It does not eliminate F as an interruption elsewhere, different mask semantics, other page keys, or a later decoding layer. The standard repeating-key outputs overlap the earlier [prime and keyword streams test](#/experiments/wulfic-prime-keyword-stream-families); the mask scan and the source's second-layer screens are the additions here.
