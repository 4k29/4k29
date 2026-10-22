# Human movie dialogue candidate — NOT admitted

During Round37, acquired only upstream JMRD TRAIN at pinned a20b0a89b4cf6ce1db320039f6e27df10604bf4c. Raw49,148,166bytes, SHA2564c8abd2e8913a7f2bc208052e8934f3af937c72636b573ea2dbfb83ec6945eaa, remain in /workspace/next-source-candidate-jmrd/upstream-train.json; reproduce using acquisition URL and verify SHA. Upstream valid/test were not acquired. No current training input or condition changed.

4,575 human-crowdworker dialogues /103,444 utterances /260 exact movie title strings. Only original dialog[].text is a potential future training source; knowledge, summaries/reviews, questionnaires and checked knowledge are excluded from prospective positives. No external generated answers. CC-BY-SA4.0, attribution Takashi Kodama, Ribeka Tanaka and Sadao Kurohashi; upstream LICENSE/README and source commit retained.

TRAIN-only structure counts found no empty/control/embedded-newline utterances, adjacent same-speaker messages or exact dialogue duplicates. This does not establish semantic quality, lack of shorter/near duplicates, broad daily-chat coverage or model benefit. Exposed README ID03042 is absent from this TRAIN, and remains excluded if any future source admits it.

Before any admission: audit against protected existing text/heldout hashes and exposed probes, retain existing train/validation/test membership, verify identity and serialization boundaries, freeze one-factor round and execute independent preflight. Neither membership, sampling mass nor a next training condition has been selected by these counts. No new TEST result. The older Round35/Round36 statements about no dialogue acquisition describe their earlier evidence and remain unchanged.

The subsequent hash-only audit protected19,952 existing documents /11,076,165 distinct128-bit hashes of64-character windows, including the existing human heldout through raw-text hygiene hashes only. All4,575 candidate TRAIN dialogues remain after this exact-length overlap check. No heldout semantic reading/tokenizer/model use, no upstream JMRD valid/test download, no short/approximate overlap guarantee and no training admission. Full receipt and executed audit code retained.

A posthoc literal-surface comparison found that the fixed8 observed generic reply strings are590/269,877 current RealPersona utterances versus976/103,444 prospective JMRD utterances. JMRD has a longer mean but shorter median utterance. This is not a complete acknowledgement classifier or causal evidence; it specifically prevents claiming that this source automatically removes generic acknowledgements. No data filtering or admission follows from this diagnostic.

## Reproduce the separately cached audits

From the repository root, run `python training/language/round37/execution/next-source-not-admitted/acquire_as_executed.py` only if the candidate cache is absent. If it already exists, verify acquisition.json and the raw SHA instead of overwriting. Acquisition creates `/workspace/next-source-candidate-jmrd` and obtains only the pinned upstream TRAIN.

The executed audit scripts resolve input/output beside themselves. Copy `audit_train_candidate.py`, `audit_protected_overlap.py` and `compare_train_surface_counts.py` from this directory into `/workspace/next-source-candidate-jmrd/`, then run those cached copies in that order. The existing historical human-source cache and original repository inputs referenced by the protected-overlap script must first be restored by their existing reproduction instructions. Copying scripts does not change their bytes or code SHA. Match the deterministic counts/input SHA with the saved receipts; UTC may differ. Never execute these scripts against upstream JMRD valid/test or use the candidate in training without a separately frozen round.
