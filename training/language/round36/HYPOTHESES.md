# Hypotheses before the completed Round36 evaluation

This is an analysis of the unchanged objective and completed Round35 evidence, not a final Round36 result. Round36 training remains in progress; no new full-generation judgment, new TEST result or adoption is recorded here. See Round35 RESULTS.md and EOS_LOCATION_DIAGNOSTIC.md for original evidence and limitations. One learning factor changes in Round36: EOS auxiliary coefficient1.0 to0.3. No follow-up condition is selected by this note.

## Competing next-token targets

At an eligible authentic human utterance end, the original unmasked gold target remains the standalone newline16. The added target is EOS2. Both CE terms use the same original valid-target denominator. Ignoring other positions, shared parameters and the other losses, this position contributes

`L = -log(p_newline) - alpha * log(p_EOS)`.

For this isolated two-target problem, the optimum has `p_EOS / p_newline = alpha`, with `p_EOS = alpha/(1+alpha)` and `p_newline = 1/(1+alpha)`. Alpha1 gives a tie; alpha0.3 favors newline, with EOS probability approximately0.231. This is a property of the local objective, not a prediction that the actual network will attain those probabilities. Other training examples, original dialogue-final EOS labels, unlikelihood terms and parameter sharing change the actual distribution.

Consequently, weaker auxiliary training can reduce damage to original gold likelihood while also weakening greedy termination. It cannot be assumed to teach a clean utterance-end rule, richer content or subject–predicate agreement. A future target-format experiment could test this conflict, but must be a separate predefined round; changing gold targets or evaluating a new serialization in Round36 would invalidate its coefficient-only comparison. The unchanged original human-DEV likelihood must still be reported if a future target-format experiment is tried.

## Spillover and repetition

The completed Round35 matched5000 diagnostic used only12 fixed TRAIN rows, with67 eligible positions. Against coefficient0, coefficient1 increased mean EOS probability there from0.032817 to0.369663, while original-gold NLL rose from0.892809 to1.328342. At1840 original content positions excluding every newline-containing token, mean EOS probability rose from0.001823 to0.012167 and EOS argmax counts from3 to45. These are descriptive selected-TRAIN-position statistics, not representative estimates for the entire corpus. EOS at a content position is not automatically an erroneous alternative continuation.

This motivates the single lower-coefficient trial and the predefined matched5000 comparison. It does not establish that spillover caused every failed generation. Round35 changed its own generated negative targets as its weights changed: global RNG, positive draws and negative prefix histories were paired, but negative completion content and length are mediated by the treatment. Direct EOS effects cannot be separated from those mediated effects using this comparison alone.

Longer output, fewer sampled repeats, more EOS events and lower NLL each require separate interpretation. An early generic acknowledgement can terminate cleanly while failing to supply requested content. A finite changing technical narrative can avoid an exact loop while failing the daily conversational context. Original gates remain unchanged.

## Other explanations and discriminating evidence

- **Capacity:** unresolved. These sibling rounds keep8layers/192dimensions/FFN768 fixed, so they cannot identify a capacity effect. Prior capacity trials must be reviewed before proposing another enlargement. Failure alone is insufficient evidence to scale.
- **Data amount and genre:** unresolved. Human TRAIN sampling mass stays30%; seven older genre masses and all positive files are unchanged. Common weighted DEV excludes expanded human-chat DEV. Report humanDEV99 and actual daily/native/source generations separately. A new human source, if justified after this result, requires its own round, license/attribution, fixed membership and leakage audit. The existing JMRD dossier is metadata only; no JMRD dialogue has been admitted here.
- **Tokenization/boundaries:** the independent147986-row audit verifies eligibility against authentic boundaries without modifying any original target. Only standalone-newline targets qualify; this is not all possible tokenizations of every utterance ending. Canonical/Glyph/random-cut40/30/30 and the5455-piece vocabulary remain fixed. No tokenizer effect is isolated by this round.
- **Optimizer/LR:** initial model, full Adam moments/counters and used RNG states are aligned with the same Round28 parent. Runtime audits check finite weights/moments and real counters. This can exclude observed corruption; it cannot establish that the fixed LR/objective is optimal. Do not change LR during this trial.
- **Context and decoding:** the42 fixed inputs are at most57 tokens; adding the fixed192-token budget stays within256. For these inputs, the generation cap binds before context truncation. This does not prove adequate learned long-range memory or adequate training context. Do not attribute those fixed-input failures to256-token inference clipping without evidence.
- **Undertraining/overfitting:** compare full fixed DEV curves and selected/terminal states. Sampled last-batch training losses are not whole-corpus means. Round35 humanTRAIN99/DEV99 gaps were not topic/length-matched and DEV contains one exact duplicate pair; a small gap alone neither proves nor excludes overfitting. No extra dose is justified by a transient rise alone.
- **Numerical error:** Round35 new selected/terminal outputs matched Python/JavaScript and raw/rounded FP32 in the measured84 state outputs. That is limited evidence; the known Round10 near-tie divergence remains recorded. Round36 numerical checks are pending and must not be claimed passed before execution.
- **Evaluation:** all fixed inputs are exposed DEV diagnostics, not new TEST. Round35 primary native8 minimal compatible speech acts3 become1 when requiring content beyond backchannels and0 under explicit referent/content demands. Source5 minimal compatible speech act1 becomes0 with content demanded and comes from one cast family. Report these sensitivities; do not pool them into an independent language-success rate or relax original17/13/9 strict gates.

## Decision after actual execution

Finish the predefined10000 actual updates, verify all retained/selected states, read every complete new selected/terminal output, compare identical conditions and preserve raw text. Then distinguish termination gains, substantive contextual language and NLL tradeoffs. Select one justified follow-up factor using those observations. Neither this note nor the isolated target-ratio calculation authorizes a claim of improved Japanese ability or adoption.
