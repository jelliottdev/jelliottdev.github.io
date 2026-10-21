# Historical walkthrough and transcription priorities

User requested broader Cicada coverage and supplied examples of failed book-code replays and uncertain page joins. Source comparison begun 21 October 2026. Public entry points: `cicada-history` and `historical-book-codes`. These are not complete independent replays.

## Next evidence to produce

1. COMPLETED: `2012-opening`, `exports/cicada-2012-opening.json` and replay script. First 2012 JPEG: pinned original bytes, appended ASCII extraction and shift, original versus duck roles, actual OutGuess payload and extraction receipt. Then a stage-specific illustrated walkthrough.
2. COMPLETED archival replay: `exports/cicada-2012-subreddit.json`, all 76 lookups and both author-selection rules. Historical provenance remains limited. Mabinogion: pin the archived Reddit JSON and the contemporary account's text; record every post ID, creation time, duplicates, excluded image posts and decoded line. Reconcile archived sorting with the contemporary spacing repair. Do not assert which fourth post a user meant without its ID. Never reorder lines solely to fit the expected phone output.
3. Blake: verify the formatted Voice of the Devil text against the full referenced plate and trace all 22 lookups. Keep the second-chance branch separate.
4. COMPLETED archived-text Liber AL replay: 44 lookups plus two literals in `exports/cicada-2013-liber-al.json`. Exact original edition, fresh image extraction and signature verification remain separate outstanding provenance work. Pinned chapter text and signed coordinate list; record numbered-verse parsing, space/newline removal, punctuation, literals and every character. Preserve raw dashes separately from URL slash interpretation.
5. Continue 2013 disk-image/data routes and 2014 pre-manuscript stages as distinct artifact transformations. Existing archive descriptions are leads, not fresh replays. Include visuals and byte hashes.
6. LP2 page joins: published `exports/page-boundaries.json` and `scripts/page_boundary_inventory.py` with exact edge slices, source hashes and explicit unreviewed status. All 55 pairs link to the reader in the transcription-checking guide. Original-image crops and visual review remain outstanding. A preliminary scan of adjacent files LP2-00 through LP2-55 removes slash markers and strips edge whitespace, then checks whether both edge characters are canonical runes. It gives 32 rune-to-rune pairs and 23 others. Left-page indices: 0,1,3,4,5,6,8,9,16,18,19,21,23,24,25,27,29,31,33,35,40,41,42,43,44,45,46,47,48,51,52,54. This is a text convention count, not proof of intended word joins or a list of contested readings. Review transitions across sections and non-runic pages explicitly.

## Sources inspected

- ClevCode contemporary 2012 account: https://clevcode.org/cicada-3301/
- Uncovering Cicada wiki: Second chance (2012), What Happened Part 1 (2013), What Happened (2012). Direct Fandom retrieval is blocked; accessible search excerpts were compared with the artifact archive. Do not claim a complete audit of these wikis.
- neuroretransmit/cicada, pinned revision `ade9a02889ef8acbc8cde8edbfd0a785c369f4c3`: 2012 subreddit script and anomaly log, book branches and second chance; 2013 opening, disk inventory and Twitter reconstruction. Read source, did not execute downloaded scripts.
- micheloosterhof/cicada-2014 stage index: archival coverage, not a current status register.

Keep literary editions distinct from the exact puzzle-derived working text. A correct title alone does not establish reproducibility.
