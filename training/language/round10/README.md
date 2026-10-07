# Raw Japanese: short word BPE experiment

This is a raw causal language experiment, not a new public answering model. The preceding round8 completed 10,000 updates and improved held-text NLL/UTF8 byte from 1.08560 to 1.00085, but first-sentence passes remained 5/13, nonloop outputs 1/13 and meaningful complete continuations 0/13. Natural Japanese has not been established. Public model weights and answers are unchanged.

## Corpus and original text

Round8's 2,549 documents and original assignments/chains are retained. Add the 287 archived, attributed Statistics Bureau/Cultural Affairs documents in round9-source, whose captured policies permit CC BY 4.0 compatible PDL1.0 reuse. Source collection details and limitations remain in that immutable phase. No Wikipedia, teacher answers, external model weights, pretrained tokenizer or external generation API is used. PyTorch implements numerical computation only.

The resulting 2,836 documents comprise TRAIN 2,209, VAL 189, TEST 234, development 202 and quarantine 2. TRAIN has 9,125 original units, 5,036,516 characters and 13,773,954 UTF8 bytes. New held groups are selected before fitting; grouping uses normalized site/author/title and exact long paragraphs. It does not certify absence of fuzzy paraphrase or short overlap. Old held assignments stay fixed. This is not a fresh wholly unseen test against every historic model.

Glyph assembly appends 103 rules to the own parent tokenizer (4,412 TRAIN glyph types; vocabulary 4,943). Short word BPE is fitted only on TRAIN, using the own adjacent-pair implementation. Candidates append 512 or 1,024 word rules (vocabularies 5,455 / 5,967), with each added piece a complete UTF8 string of at most 18 bytes. Existing IDs and ranks stay fixed. No linguistic dictionary or pretrained segmentation is used.

TRAIN has a canonical view and a deterministic alternative with 10% of word rules omitted. Both reconstruct the identical source bytes with true BOS/EOS and complete causal label coverage; they are duplicate segmentations, not extra independent text. Sampling masses are .85/.15. VAL/TEST use canonical segmentation only. Word pieces may cross a supplied prefix boundary, so character token cut invariance is no longer assumed.

Canonical target counts: 3,530,804 / 3,176,179 (512 / 1,024 rules), versus 5,045,641 glyph targets. Fewer tokens is a representation property, not evidence of faster training, better Japanese or lower hardware latency.

## Initialization, plan and evaluation

Copy only the own verified round8 selected 8-layer/192-dimensional weights (selected lineage 28,000 updates), preserve old glyph rows, initialize added glyph rows to zero and added word rows to .95 times own constituent glyph-vector means. Every parameter remains trainable. Old-ID logits are checked against the parent; new word segmentation and positions change, so new-encoding logits/NLL are not claimed identical. Baselines must use the same new representation.

Frozen plan: two independent 1,000-update pilots, seed2029, LR .00015, fresh AdamW; choose vocabulary and saved pilot checkpoint by canonical VAL NLL/UTF8 byte only, not token perplexity or generated output. Then perform 10,000 additional updates from that own selected pilot with fresh AdamW and seed2039. Completed updates on different pilot branches are counted separately from selected weight lineage. Checkpoints save every 100 updates, and contain optimizer counters/RNG for exact resumes. Planned updates are never reported as completed updates.

Raw greedy VAL continuations permit the full vocabulary, special tokens and unknown-byte pieces; no output rewriting, fixed answers, retrieval, generated text filters or repetition repair. Expanded VAL17 (including new stat/bunka examples), parent13 and original9 must each satisfy narrative/modern sentence, nonloop and full-meaning gates. First-sentence closure and nonloop alone cannot prove coherence. No TEST34 continuation or instruction/QA tuning before language stability. Manual judgments must bind unmodified generation hashes and disclose assistant rather than independent human scoring.

`generation-policy.json` retains the inherited historical `freshTest` description for provenance. Its statements about fresh random initialization describe the older round3 experiment, not this warm start. The current comparison, frozen continuation fields, own initializer and this document define the actual round10 protocol. No TEST generation has been opened in this phase.

## Verification and frozen source snapshot

`test_word_bpe.py` compares the optimized fitter with an independent naive implementation on overlap/tie/max-length fixtures. `test_preflight.py` verifies every original stream and causal target, held segmentation isolation, inherited units/folds, owned parent initialization/logit compatibility, TRAIN gradient flow and sampler probability masses. These checks make zero optimizer updates. The first preflight run had a test-module import-path error, corrected before training; the failure summary and passing log are retained.

`source-manifest.json` freezes preparation sources/data/policies and preflight evidence only. Active run checkpoints and results are excluded. Completed training/results require their own later audited manifest and measured language review.
