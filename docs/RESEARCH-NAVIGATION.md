# Research navigation and evidence access

The reference serves researchers who may know a number, visual feature, spelling, or source filename before they know a page identifier. Retain traditional wiki typography and compact navigation. Favor meaningful links and tables over dashboard cards.

## Observed reference friction

Comparison inspected 19 October 2026:
- https://www.cicadasolvers.com/wiki/liber-primus/ provides release descriptions, page lists, and image galleries.
- https://www.cicadasolvers.com/quickstart/ provides a broad briefing spanning facts, methods, and hypotheses.

These are useful starting points. This is a bounded comparison of those pages, not a claim that every other wiki lacks the features below. Our archive work repeatedly needed additional context: filenames in combined archives versus release numbering, literal rune labels versus contextual English, corrections to inherited transcriptions, exact counting conventions, and the provenance behind a reading.

## Implemented journeys

| User knows | Entry | Destination |
|---|---|---|
| An image detail such as infinity or 3299 | Search or Research topics | Matching observation, page details, original image |
| An archive filename such as 32.jpg | Page numbering | LP2-15 and pinned source files |
| A known passage | Known readings | Section, individual pages, literal and contextual text |
| A possible transcription error | Correction filter or topic | Archived text, correction, evidence record |
| A method name or key question | Known readings / counting topic | Formula, key, sequence continuation, copied positions, provenance |
| A source subject | Search or source filter | Captured public reference link |

Page details also expose related topics, neighboring pages at the top and bottom, section links, and a copyable citation. Search shows match context and includes visual notes and corrections. Filters persist in the URL and survive reloads. Multi-page contextual readings are explicitly identified as section readings in search results.

## Content maintenance

`data/topics.json` is an editorial index of supported facts and the questions they answer. Update it deliberately when adding researched evidence. The archive importer regenerates records and search metadata but does not overwrite this editorial index. Every new topic needs source links and a statement of its evidence scope.

Never promote a provisional geometry proposal, decoded guess, or literature resemblance into an established observation. The initial visual inventory covered LP2-00 through LP2-02 and selected LP2-15 regions; later coverage is recorded in `data/evidence/editorial-page-notes.json` and linked guides. Inspect those current records rather than treating this initial inventory as a coverage limit. The presence of a page record or an observation does not make its inventory exhaustive.

## Validation

- Desktop 1440px and mobile 390px rendered and inspected.
- Topic → correction section; infinity → page 15; 32.jpg → LP2-15.
- Filter persistence across reload, all nine reading sections, searchable source directory.
- Seven mobile routes checked for document overflow, plus menu and image viewer interactions.
- All 17 literal known readings independently reproduced using the exposed parameter records and the separately documented LP1-10 correction.
- Original 75 image checksums verified in the initial build; image assets unchanged by this update.

The site is published through the repository's GitHub Pages workflow. Verify the current push and deployment state when reporting publication; the initial sign-in dependency is historical. A local preview and repository ZIP remain available for offline use.
