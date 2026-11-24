# Everyday-language diagnostic review protocol

Fixed before inspecting either model's outputs on daily-probes.json. This is additional exposed DEV, not a new TEST, training target, checkpoint selector, or replacement for the unchanged Round10 strict language gate.

Read every complete prefix and continuation from both models. Retain all raw token IDs/text/EOS/UTF-8 validity and the generation/model hashes. Do not repair outputs or hide trailing collapse. If outputs are identical, record that fact; do not manufacture an improvement.

For each output describe:

1. Japanese word order, inflection, and grammatical naturalness.
2. Subject/predicate and modifier relationships, allowing ordinary Japanese ellipsis.
3. Meaning within sentences and across the entire continuation.
4. Connection to the opening; for chat, whether it naturally responds to the previous speaker.
5. Topic continuity and reference to the recent conversational context.
6. Exact and paraphrased repetition, separating natural acknowledgments from long repetitive loops.
7. Any point where meaning or topic collapses, including after an initially natural answer.
8. EOS, context/length truncation, and numerical/UTF-8 limitations separately from semantics.

A short natural reply need not contain multiple sentences. Creative, plausible details are not automatically language failures; factual accuracy is not certified. Unknown proper names or unverifiable claims alone do not establish grammatical failure. Changed wording, lower NLL, shorter output, or EOS alone do not establish better meaning. Do not infer new-speaker or unseen-human-conversation generalization from these assistant-authored diagnostic openings.

Report the existing 17-probe strict gate separately. Do not invent an easier gate or declare daily-chat readiness from these twelve diagnostic outputs. No composite score or deployment threshold has been assigned to this supplementary set.
