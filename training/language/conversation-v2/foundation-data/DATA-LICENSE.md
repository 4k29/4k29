# Source-specific data terms

The archives and derived candidate corpus retain their original source terms;
this directory does not assign one blanket license to all source text.

- JaQuAD TRAIN: CC BY-SA 3.0, Skelter Labs / JaQuAD authors. Preserve the
  publisher README/LICENSE in `sources/`, pinned dataset revision, article titles,
  URLs and original human question/answer IDs. Wikipedia-context attribution and
  third-party quotations need additional admission review.
- Japanese Wikibooks and Wikivoyage: official Wikimedia 20261001 dumps, CC BY-SA
  4.0 according to the recorded rights APIs and Terms of Use. Original revision
  URL, history URL, last contributor metadata and raw wikitext hashes are retained
  per derived article. See the full text and source evidence in `sources/`.
- Source quotations, imported material or exceptions are not silently relicensed.
  Raw archives preserve the source context; the derived corpus does not certify
  that every quoted work has identical permissions.
- Existing RealPersonaChat/JMRD remain existing assets under their recorded terms;
  they are not counted as newly collected text here. No new rights are inferred.

All three new sources remain **candidate-not-admitted**. Dataset acquisition,
normalization, token counting and a zero-update numerical audit are not model
training admission, human-only authorship certification, or permission to deploy
an assistant. Source metadata, dates, hashes, transformations and unresolved
conditions are in `catalog.json`, `SOURCES.md`, pipeline receipts and the report.
