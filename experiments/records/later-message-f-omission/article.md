# Does omitting F make both later messages prime length?

**Result.** Yes, under the declared Gematria Primus transliteration. The preserved 2016 and 2017 signed-message bodies encode to **177** and **45** rune indices. Each contains four F runes. Removing every F leaves **173** and **41**, both prime. This reproduces the reported counts, but it is an observation about two known messages, not a decoding rule for Liber Primus.

![A compact comparison shows the original 2016 and 2017 message lengths and the lengths after omitting F or W.](experiments/records/later-message-f-omission/omission-counts.svg)

The messages are stored as **Latin-letter text**. This record uses the site's explicit GP encoding: split into letter runs, map V to U, then take each word's unique shortest encoding with the archived rune aliases. It counts the message body before PGP signature armor, including the sign-off and verification text. A different transliteration or a different body boundary could change the count; neither source message contains literal runes to count directly.

To see whether prime lengths are specific to F, the script applies the same one-symbol removal to **each of the 29 GP runes**. Two omissions leave prime lengths in both messages: F gives 173 and 41, while W gives 173 and 43. The full [result](experiments/records/later-message-f-omission/results.json) records all 29 pairs. This is a finite comparison, **not a p-value** for intent: F was already a salient symbol in the puzzle, and these two messages were selected from a larger history.

The [plan](experiments/records/later-message-f-omission/plan.json) fixes the body, encoding and one-symbol comparison. The script reads the preserved signed payloads and verifies their hashes through the existing [message manifest](data/evidence/later-messages.json). From the repository root, run `python experiments/records/later-message-f-omission/run.py --check`. The public [later-messages guide](#/wiki/later-messages) explains source preservation and signature verification. Prime lengths alone do not say which LP2 positions an F should skip, whether a key advances, or what plaintext should follow.
