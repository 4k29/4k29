# Round38 results — common NLL improves; daily meaning does not

Actual10000 optimizer updates completed once, without a training restart. The selected state is9500 (Adam29500, weight lineage68500); terminal10000 has Adam30000/lineage69000. Training elapsed9578.906s on CPU2/FP32/batch8. UI connection interruptions did not stop the detached trainer or cause repeated updates. Do not add sibling-round doses to these weight lineages.

**Common DEV NLL improves, but the everyday target fails. Not adopted.** The research adoption anchor remainsR25; public model/site unchanged. All measurements are exposed DEV, not fresh TEST or independent blind human evaluation.

## One learning factor and checks

Append4575 original human JMRD official TRAIN dialogues (103444 utterances,3126150 serialized characters including inserted separators,9180600 UTF-8 bytes), pinned `ku-nlp/JMRD@a20b0a89b4cf6ce1db320039f6e27df10604bf4c`, CC-BY-SA4.0/Kodama–Tanaka–Kurohashi. Use only original `dialog[].text`, joined by newline; no roles, reviews, knowledge, questionnaire fields or generated positives. Upstream valid/test were not acquired. Licensing/provenance, exact extraction and protected-hash receipts are in `added-human-source/`.

All old TRAIN bytes/index rows/documents and validation/tokenizer bytes remain exact. Own8x192/head4/FFN768/context256/4655808parameters/vocab5455, BPE40/30/30, same aligned R28 full model/Adam20000/Torch/private Python RNG, LR2.2499999999999998e-5/seed lineage2049/wd.05/clip1,10000 dose, mixed-view common-DEV selector every500, greedy192 inference, teacherUL1/selfUL.1every10/64tokens, human endEOS.3 and eligible original-newline mainCE exclusion are unchanged. Core learning files are byte-identical toR37. No external weights/tokenizer/API/teacher or output repair.

Before launch:37 meaningful unit contracts passed; every new view recovered original bytes with exact target coverage; all189166 TRAIN rows passed independent prefix/end-mask checks; every old true-end list was preserved and new ends use exact existing token boundaries only. Same legacy-row objective terms matchedR37; actual new JMRD rows gave finite nonzero gradients in all parameters. Exact model/moments/RNG restoration and full initial DEV0.9718989571266189 were verified before any update. All389 frozen inputs remain SHA-bound; final verification checks them again.

Human-chat mass remains30%, other genres70%. Corpus addition naturally changes the within-human population: expected JMRD mass about9.955% overall and existing RealPersona20.045%, not its prior30%. Actual80000 sampled rows include8005 JMRD and16063 RealPersona. Independent replay exactly matches this experiment's private sampler RNG,15630059 original targets/54509117 target bytes and150421 eligibleEOS positions/9171 batches. Positive draws/final Torch and sampler RNG differ fromR37 as expected. R37 targets15584824/54383388 bytes; equal updates are not equal token exposures. This is one corpus intervention, not separate identification of quantity, topic, source quality or effective dose.

Self-negative calls1000/generated tokens38393/repeated target positions14139 are saved separately and never positive teachers; R37 had1000/37969/14000. Changes in generated negatives are endogenous effects of the data intervention. Midpoint5000 own sampler/RNG/positive/EOS replay also matched exactly. JMRD3627/4575 source units were touched, which does not mean all targets within them were seen.

## Fixed old/new measurements

| State | Common mixed-view DEV NLL/byte | Authentic everyday DEV99 NLL/byte | Same legacy human TRAIN99 sample |
|---|---:|---:|---:|
| R37 selected8000 |0.9677085223|0.9330181026|0.9031740020|
| R38 selected9500 |**0.9650132993**|**0.9403877238**|0.9138056528|
| R37 terminal10000 |0.9689081227|0.9319026966|0.9013179347|
| R38 terminal10000 |0.9651763738|0.9406002860|0.9142599399|

The common selector excludes the added human DEV and was not changed after viewing these results. The selected human DEV regression is+0.0073696212/byte;82/99 nominal files worsen,17 improve, median per-file delta+0.00915838. These are descriptive repeated-speaker/duplicate-containing DEV files, not99 independent population observations. TRAIN99 is the same old RealPersona sample, not new JMRD or all expanded TRAIN; topics/lengths are unmatched and DEV has one exact duplicate pair. A smaller TRAIN/DEV gap while both losses rise does not prove better generalization or less overfitting. Original serialization and total NLL/guards are retained, including newline cost; no body-only or EOS-substituted selection.

Every new selected42 and terminal42 full prefix/continuation was actually read. They contain79 distinct prefix/full-text pairs; all five exact duplicates have identical judgments. All168 four-state outputs are saved without trimming in [ALL_FOUR_STATE_GENERATIONS.md](execution/ALL_FOUR_STATE_GENERATIONS.md), with raw tokens in JSON. Regenerated old selected42 raw cores exactly matchR37 historical outputs; old selected/terminal judgments retain verified SHA provenance. This is not claimed as a fresh blind rereading of old84.

| State | Original17 first / nonloop / whole meaning | Daily12 whole / long loops / EOS | Native8 minimal acts / loops / EOS | Source5 minimal acts / loops / EOS |
|---|---|---|---|---|
| R37 selected8000 |10 /3 /1|0 /5 /7|2 /1 /7|1 /2 /4|
| R38 selected9500 |9 /5 /1|0 /6 /7|2 /1 /7|0 /1 /4|
| R37 terminal10000 |6 /5 /0|1 /7 /5|1 /3 /6|0 /2 /4|
| R38 terminal10000 |8 /3 /1|0 /4 /8|3 /0 /8|0 /2 /4|

Native successes are mostly acknowledgements and a shared taste opinion. New selected/terminal content beyond backchannel is1/1, meaningful explicit context-object references0/0 and new-information responses0/0. Source5 are ONE cast family/three public pseudonymous IDs, not five independent groups. More EOS/nonloops/minimal acknowledgements do not establish substantive conversational ability. Original17/13/9 and both narrative/expository strict gates fail for both states.

The new selected original meaningful sentence is a genuinely coherent short policy completion: prefix `本節1を支える取組として、金融機関も含めた循環分野の経済活動に`; entire generated text `必要な資源を創出する取組を推進します。` thenEOS. It is not daily-chat readiness or certified policy truth. The terminal meaningful original is a single method-returning-method sentence with opaque `Inter` name, allowed by the same fiction/unknown-name rule asR37; an opaque-name-strict alternative gives0. No factual API correctness is certified.

Failures include the entire selected meeting reply `「おいしい」と言うのです。` to a request for a meeting time, and the entire native storage/memo reply `そうですね。それはどんな映画を見てみたいですか？`. No correction or continuation is appended by the evaluator. The full failed looping prose and trailing collapse remain in the canonical full-text artifact.

## Ambiguity and unchanged acceptance

Manual records retain per-row reasons and raw-pair SHA. Selected finite changing numeric, warning and cultural-policy lists are primary nonloops despite intrusive repetition; treating all three as loops gives2 rather than5 nonloops. Treating the finite AI-policy list as nonloop gives6. Selected JMA08 can be read as tool ellipsis, giving weak whole2 instead of1. Cold-escape/passive-honorific first-sentence sensitivities give11 instead of9 first passes. Terminal short URL recursion can give2 rather than3 nonloops; opaque-name strict whole0 and tool-ellipsis weak whole2 are recorded.

Selected daily dinner has an unstated-other-person question alternative1; primary0 remains. Terminal fatigue's51-token finite food fragment and park's15-token triple possessive are primary nonloops with intrusive repetition; counting either gives5 loops, both6 instead of4. This distinguishes them from selected park's5 repetitions andR37 terminal's6, not an EOS-only rule. Native vague actress questions can add one weak act; terminal short taste repetition can count as one loop instead of0. Source additional-place/motivation questions can yield weak0–2 rather than primary0. None passes strict gates or the authentic-human NLL guard, so no favorable sensitivity is used for adoption.

Primary Pareto versus scientificR37 fails (first10→9), versus adoptedR25 is true (8/4/0→9/5/1 and lower NLL). That is not promotion: strict gates fail and the unchanged practical humanDEV bound **≤0.9107185711429243** fails. Fixed daily whole≥0 and nonloop≥4 pass, but paired-control daily nonloop7→6 and human NLL worsen. No optional NLL-only adoption; anchorR25/public/site unchanged.

## Cause analysis

- **Data quantity/genre:** leading supported hypothesis is source interference/dilution, not proof that human text addition always helps. Common NLL improves while authentic everyday TRAIN/DEV worsen. RealPersona exposure falls to about20% while movie dialogues take about10%. Posthoc literal `映画` appears in3 selected/2 terminal supplementary replies versus0/0 inR37; this is a small descriptive word check, not a complete topic classifier or new gate. Movie-biased raw data also has more literal acknowledgements. Quantity, source style, topic and changed stochastic exposure are not separately identified by this one trial.
- **Capacity:** fixed4.66M parameters; cannot rule out limited capacity or competing-domain interference. PriorR27 FFN768→1536 did not establish daily meaning. Current metrics alone do not justify enlargement.
- **Tokenization/character boundaries:** exact bytes, all three views, original label coverage and end/prefix alignment passed. Changed safe prefixes decode correctly. This rules out the audited data-corruption hypotheses, not poor token efficiency or optimal segmentation; word-piece fraction is not a meaning score.
- **LR/optimizer:** full parent model/moments/RNG, finite real gradients/states, Adam30000, independent sampler replay and unchanged coefficients argue against failed updates or observed state corruption. They do not establish optimal LR/objective.
- **Context:** fixed42 prefixes and192 continuations fit context256, so observed inference clipping is not their trigger. Long-range learned context use remains unresolved. Daily role-labelled openings differ from raw human serialization, but actual native/source contexts also fail substantive grounding, so formatting alone does not explain the results.
- **Dose/overfit:** common DEV improves nonmonotonically with selected9500 rather than terminal10000; new data is not exhaustively seen. Legacy human TRAIN and DEV both worsen, which does not support a simple heldout-only overfit explanation. PriorR33 extra dose improved NLL but not daily meaning. No blind dose extension chosen.
- **Numerics:** all84 new full sequences match Python/JS and rawFP32/seven-decimal export. Measured reference errors are within unchanged2e-4. These particular failures are not explained by an observed export divergence; no universal hardware/argmax guarantee is claimed. HistoricalR10 near-tie16/17 remains disclosed.
- **Evaluation:** common DEV selection misses the practical human domain; retained selector can optimize the wrong target. Fixed exposed small sets, one source cast, one DEV duplicate pair and assistant—not blind independent human—judgments limit inference. Natural acknowledgements are separated from meaningful new content; lower NLL/nonloop/EOS is never substituted for semantic success. A separate selector study must not be combined with source reweighting.

The next **unexecuted** one-factor proposal is within-human source balance: RealPersona25%+JMRD5% overall, preserving human30%/other70% and everything else. Halving the movie share tests source dilution while retaining added text. See [NEXT_EXPERIMENT.md](NEXT_EXPERIMENT.md); no next-round updates are claimed.

## Numerical/repository evidence and identities

New selected42/42 plus terminal42/42 match Python/JavaScript AND rawFP32/seven-decimal export. Maximum measured new reference-logit error is1.239776611328125e-5 for Python/JS and2.6226043701171875e-5 for raw/export, within unchanged2e-4; sampled reference positions are not a bound on every step/hardware. Old current JS scope42 and raw scope25; old original17 raw not rerun, old terminal evidence historical. R10 near-tie reference SHA `117e5f69480f8856262090b46825efb9a2333732791c88e9a8b7484a8e406769` preserves recorded16/17 strict parity without repair.

Pretraining37 contracts and repository962 tests passed; existing public behavior43 questions/2580 replies passed read-only. These public checks do not measure the experimental LM. Final PR CI is recorded separately for its actual commit. Historical automatic pending records are retained; `final-assessment.json` and SHA-bound manual records define final semantic status. Unused inherited helper metadata/diagnostic scopes are clarified in `diagnostic-metadata-scope.json`; the authoritative four-state assembly uses the correct corpus-only condition.

- Initial alignedR28 parent: `2870e80b4bd5973555dd570cb7195f670f56d670cdd10a51f153fe889ae85204`.
- Final policy: `7c0883088ed47f20fb481f07a5c4fe6d5f471f8033ed19d0ddc85815bcf05d1d`; frozen input manifest: `c2f62acc0b1ead64c4f59d13e816378bb1d56307511be6aac3245ad38a08d6a2`.
- Core trainer: `7d72e9d8868b8b7240bc311b29ed0d7a9266a7429a5b619be8b5caa3ee483a29`; TRAIN tokens: `a465b071db720c46d1efe74821e4a9609d19e183f2af35f290f4681e17e63a98`.
- Latest full10000 checkpoint: `501539cb042a59fed588570e333bd79386281128dcda18c6f66cb0f16cc556c5`; selected full9500: `871d9ce5de6b4ad4595926efdd07605c6749306cc5c280f30b32596d09fc25e5`.
- Selected raw weights: `a0954e55d0b6e4c2cf8d85983cb29f70b83456281c985f938d7a3a7b4078885b`; selected JS: `e339a0ee2615be809cda3fe8d913ad405ae6d23a67889e101e1e27a03bd64b2e`; terminal JS: `8b1ad194886e8159d99a46eebf7cf3630324693cdd53adc2a90a4ed425e5d93c`.

Full initial/200/1000/5000/selected/latest states are retained with model, AdamW and Torch/private Python RNG in lossless parts. No new TEST, external model/tokenizer/API/teacher, response retrieval/template, public replacement or generated-text correction was used.
