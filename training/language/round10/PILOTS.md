# Completed short-word pilots

Two independent own-weight pilots completed 1,000 optimizer updates each. Both FP32 model/optimizer states, all AdamW counters, saved RNG, initial0 empty optimizer and source identities were verified. Actual completed pilot updates: **2,000**; selected weight lineage: **29,000** (own round8 lineage28,000 plus selected pilot1,000). The rejected pilot is counted as physical learning, not selected lineage.

| Word rules | Vocabulary | Parameters | Initial canonical VAL NLL/byte | Selected NLL/byte | Selected step | Elapsed seconds |
|---|---:|---:|---:|---:|---:|---:|
| 512 | 5455 | 4655808 | 1.417879 | 1.073218 | 1000 | 560.79 |
| 1024 | 5967 | 4754112 | 1.460369 | 1.087945 | 1000 | 568.7 |

512 word rules selected using canonical VAL NLL/UTF8 byte only, before any generation. The difference is small, and this pilot budget does not establish the best vocabulary after longer training. Token perplexity is not compared across vocabularies. Elapsed times include initialization/validation/compilation/export and are not a controlled speed benchmark.

10,000-update main training starts from the selected pilot with a fresh AdamW optimizer and seed2039. That active run is excluded from this completed-pilot snapshot; its requested updates are not claimed complete. Both pilots use seed2029 and the frozen same numerical/training protocol.

No raw development/test generation or QA/instruction tuning occurred during selection. No natural conversation quality improvement is claimed. Public site model/answers are unchanged. No Wikipedia, external weights/tokenizer/API, teacher outputs, retrieval, fixed answer or output rewriting was used.

Round3 onward completed branch counters through these pilots:46,000; physical lower bound46,100 includes at least100 discarded round8 updates, with additional unlogged round8 discard unknown. These are not whole-lifetime counts and exclude the active main run.
