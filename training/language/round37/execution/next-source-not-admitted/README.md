# Human movie dialogue candidate — NOT admitted

During Round37, acquired only upstream JMRD TRAIN at pinned a20b0a89b4cf6ce1db320039f6e27df10604bf4c. Raw49,148,166bytes, SHA2564c8abd2e8913a7f2bc208052e8934f3af937c72636b573ea2dbfb83ec6945eaa, remain in /workspace/next-source-candidate-jmrd/upstream-train.json; reproduce using acquisition URL and verify SHA. Upstream valid/test were not acquired. No current training input or condition changed.

4,575 human-crowdworker dialogues /103,444 utterances /260 exact movie title strings. Only original dialog[].text is a potential future training source; knowledge, summaries/reviews, questionnaires and checked knowledge are excluded from prospective positives. No external generated answers. CC-BY-SA4.0, attribution Takashi Kodama, Ribeka Tanaka and Sadao Kurohashi; upstream LICENSE/README and source commit retained.

TRAIN-only structure counts found no empty/control/embedded-newline utterances, adjacent same-speaker messages or exact dialogue duplicates. This does not establish semantic quality, lack of shorter/near duplicates, broad daily-chat coverage or model benefit. Exposed README ID03042 is absent from this TRAIN, and remains excluded if any future source admits it.

Before any admission: audit against protected existing text/heldout hashes and exposed probes, retain existing train/validation/test membership, verify identity and serialization boundaries, freeze one-factor round and execute independent preflight. Neither membership, sampling mass nor a next training condition has been selected by these counts. No new TEST result. The older Round35/Round36 statements about no dialogue acquisition describe their earlier evidence and remain unchanged.
