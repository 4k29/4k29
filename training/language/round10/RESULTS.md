# Raw Japanese short word BPE results

Natural Japanese established: **False**. Completed updates: **12,000**, comprising two distinct 1,000-update pilots and 10,000 main updates. Selected weight lineage: **39,000**. Planned counts and updates on the rejected pilot are not represented as selected lineage.

## Canonical held-text likelihood

| Stage | Word rules | Completed updates | Initial NLL/byte | Best NLL/byte | Selected step |
|---|---:|---:|---:|---:|---:|
| word-512-pilot-1000 | 512 | 1000 | 1.417879 | 1.073218 | 1000 |
| word-1024-pilot-1000 | 1024 | 1000 | 1.460369 | 1.087945 | 1000 |
| word-512-continue-10000 | 512 | 10000 | 1.073218 | 0.966512 | 10000 |

Vocabulary 512 selected by canonical VAL NLL/UTF8 byte only, before generation. Token perplexity across the two vocabularies is not a fair selection metric. The main0 raw baseline already contains 1000 selected pilot updates, with fresh empty main optimizer state. It adds zero main updates.

| Site | Main0 NLL/byte | Selected main NLL/byte |
|---|---:|---:|
| aozora | 1.245094 | 1.186017 |
| bunka | 1.047982 | 0.910523 |
| env | 0.881195 | 0.795480 |
| jma | 1.004749 | 0.967681 |
| mdn | 0.971313 | 0.812468 |
| mic | 0.940708 | 0.841684 |
| stat | 1.131055 | 1.002544 |

## Raw continuations

| Model | Scope | Sentence passes | Nonloop | Meaningful full outputs | Language gate |
|---|---|---:|---:|---:|---|
| main-initial-0 | expanded17 | 3/17 | 1/17 | 0/17 | False |
| main-initial-0 | parent13 | 3/13 | 0/13 | 0/13 | False |
| main-initial-0 | original9 | 2/9 | 0/9 | 0/9 | False |
| word-512-continue-10000 | expanded17 | 3/17 | 2/17 | 0/17 | False |
| word-512-continue-10000 | parent13 | 3/13 | 2/13 | 0/13 | False |
| word-512-continue-10000 | original9 | 2/9 | 1/9 | 0/9 | False |

All17, inherited13 and original9 must pass separately in narrative and modern prose. Full meaning is required in addition to grammar, sustained connection and absence of loops. Short first-sentence closure does not establish coherence. These are assistant manual judgments, not independent human assessment. Unmodified raw outputs, every token ID and Python/JS parity evidence are retained. Unsupported factual claims are not certified as true.

No TEST34 generation, QA/instruction tuning or public model replacement occurred. No Wikipedia, external weights/tokenizer/API, teacher text, retrieval, fixed response or output rewriting was used.

## Reproducibility and limits

Own random-initialized ancestry is verified through round8; all source/data/policy hashes are fixed. Every AdamW counter equals its actual branch count. Model weights and optimizer moments are FP32; training activations use BF16, CPU2. Training corpus, word vocabulary and sampling differ from round8, so cross-round changes cannot be assigned to a single factor.

Round3 onward confirmed completed branch counters: 56,000; physical execution lower bound: 56,100, including >=100 discarded round8 updates. Some unlogged round8 discarded updates remain unknown. These are not whole-lifetime totals. Any later interruption/recovery must be audited separately before publication.

Exact trimmed paragraph audit found56short paragraph types shared between TRAIN and held folds (128held occurrences), and zero shared paragraph types of at least80characters. Frequent browser/PDF notices also remain. These limits are documented in corpus-quality-diagnostic.json; they are not retroactively removed from this frozen experiment. Source-preserving duplicate TRAIN segmentations do not enlarge independent text coverage. Exact-title/long-paragraph grouping does not rule out fuzzy or short overlap. Generation timings are recorded CPU measurements, not controlled browser speed comparisons. Fewer subword tokens does not by itself prove faster or better answers.

Selected checkpoint SHA256: `9e29821c608a49e4aa2ac90619a84e574454390481c89f3e063e1e009ae62bc0`.

## Numerical comparison failure

The frozen evaluate_validation.py pipeline exited with status1 because trained full greedy sequence parity was false:16/17 Python/JS continuations matched, while validation-jma-08 diverged at generated index75. All recorded initial reference logits still satisfy2e-4 tolerance. At the common98-token prefix, Python chose 場合 over １ by9.5367431640625e-7; JavaScript rounded the two scores to a tie and chose the lower token ID. Common-prefix maximum absolute logit error is7.271766662597656e-6. The original outputs, failed pipeline log, strict evaluator and failure flags remain unchanged. The later auditor reports this failure rather than aborting the failure report; it does not relax the frozen language/parity criteria or rewrite output.

First-sentence passes stayed3/17 (original9:2/9); narrative first-sentence passes fell1/3 to0/3. Nonloop outputs rose1/17 to2/17, but meaningful full continuations stayed0/17. This is not evidence of established natural Japanese. No TEST generation or instruction tuning follows this failed gate.
