# Round36 results — coefficient0.3 rejected for daily conversation

Actual optimizer updates **10000/10000**, elapsed10280.03s. Selected8000 (Adam28000) and terminal10000 (Adam30000) full model/moments/Torch/private Python RNG are separately saved. Same aligned Round28 parent, own8x192 model,5455-piece tokenizer, BPE40/30/30, human mass30%, LR/seed/other losses/data/inference and strict gates. Only EOS auxiliary coefficient1.0→0.3 changed.397 frozen inputs verified; no external weights/tokenizer/teacher API, new TEST or public/site change.

## Complete raw generations and actual reading

All84 new selected/terminal state outputs were read in full. All168 old/new state outputs are in execution/ALL_FOUR_STATE_GENERATIONS.md; SHA-bound manual reasons and per-prefix/full-text hashes are saved. Old selected readings are reused only after exact full-core identity; old terminal provenance remains frozen historical evidence. One exposed DEV seed is not independent generalization evidence.

| Metric | R35 selected | R36 selected | R35 terminal | R36 terminal |
|---|---:|---:|---:|---:|
| Common DEV NLL/byte | 0.967821330452 | 0.967741139007 | 0.969065270309 | 0.968977461408 |
| Original17 first-sentence pass | 10 | 10 | 7 | 7 |
| Original17 nonlongloop | 3 | 5 | 4 | 4 |
| Original17 whole meaning | 0 | 1 | 0 | 0 |
| Daily12 whole meaning | 0 | 0 | 0 | 0 |
| Daily12 long loops | 8 | 12 | 10 | 11 |
| Daily12 EOS | 4 | 1 | 2 | 0 |
| Native8 whole meaning | 3 | 0 | 0 | 0 |
| Native8 long loops | 2 | 8 | 5 | 8 |
| Native8 EOS | 7 | 0 | 5 | 0 |
| Source5 whole meaning | 1 | 0 | 1 | 0 |
| Source5 long loops | 2 | 5 | 2 | 5 |
| Source5 EOS | 4 | 1 | 3 | 0 |

Original17/13/9 and narrative/contemporary gates all fail for both new states; thresholds unchanged. Selected original11 is one finite grammatical method-returning-method sentence. It is counted under the existing rule permitting coherent invented names; the real API claim is not certified. Treating its opaque name as disqualifying gives0 rather than1. The circular JMA08 threshold explanation fails primary; weak alternative interpretation gives2 total. Terminal opaque project name/omitted warning agency alternatives give1–2 rather than primary0. These alternatives do not pass the gates.

Selected daily12 has12 long loops (11 if its finite-changing tired narrative is permitted), versus8 before. Terminal daily12 has11 (the changing earthquake narrative is primary nonloop), versus10. Native8 whole meaning falls from3 minimal compatible acts to0; all8 new outputs loop. Source5 falls from1 minimal act to0; all5 primary loop (selected short54-token exchange may be nonloop under a permissive finite-exchange interpretation). Source5 is one cast family/3 public IDs, not5 independent groups. No pooled independent success rate.

## Likelihood, termination and causes

HumanDEV99 selected NLL improves 0.910718571143→0.907387109640; terminal0.903918457117. TRAIN99 sample0.871340418632, terminal0.866585185296. These are not whole-TRAIN estimates, length/topic matched samples or proof of overfitting; DEV contains one exact duplicate pair. Common DEV excludes expanded human conversation. Sampled100-step train losses are last-batch objectives, not all-update means.

At matched5000 the same12 TRAIN rows reproduce both old controls exactly. Eligible67 positions: EOS argmax37→0 when coefficient1→0.3, mean probability0.369663→0.174615; original newline NLL1.328342→1.049059. Non-newline content1840: EOS argmax45→19, mean0.012167→0.005639, gold NLL3.294975→3.285626. This supports reduced EOS pressure/gold-CE competition, not better meaning. EOS at a content position is not automatically incorrect. See EOS_LOCATION_DIAGNOSTIC.md; selected small correlated TRAIN subset, no heldout/generation inference.

At the exact eligible position the competing terms are -log p(newline)-alpha log p(EOS), with common denominator. Ignoring other losses/examples/shared parameters, the optimum ratio p(EOS)/p(newline)=alpha. Alpha0.3 therefore favors newline. The actual finite-output losses are consistent with that conflict but also mediate changed self-generated negative targets; those effects are not isolated. Do not simply keep sweeping coefficients.

Capacity is unchanged and unresolved; prior FFN trial did not establish daily meaning gains. Data genre/volume and BPE segmentation are unchanged and unresolved; no JMRD dialogue admitted.147986-row boundary audit verifies the eligible mask, not optimal segmentation. Matched model/Adam/RNG, finite weights/moments and same exposure counters exclude observed state corruption but do not establish optimal LR. The42 prefixes have at most57 tokens, so192 new tokens fit within256: generation cap binds before context clipping in these probes. Learned long-range capacity remains unresolved. Similar nonmonotonic common-DEV curves and the99-row gaps do not justify a blind extra dose. HYPOTHESES.md separates these explanations.

## Numerical/reproducibility limits

New selected42/42 and terminal42/42 full sequences match Python/JavaScript and raw/7-decimal export. Max measured reference error1.33514404296875e-5 within unchanged2e-4 tolerance; this is not a bound on all positions/hardware. Historical Round10 near-tie divergence16/17 is retained in round11/execution/old-numerical-divergence.json. Old current exported Py/JS scope42, raw scope25; old original17 raw not regenerated, old terminal evidence historical. No text repaired. Initial/200/1000/5000/selected8000/latest10000 six states have lossless parts. Latest checkpoint 1ae20c82c181512674aba480779e4ebb1fbb9d785abcb810fba2179d900d7185; selected 9110d5f7d289ca36d2ed4cb5223dda3ffaa08932683b374d1886f437edf58e2b. Data/code SHA and actual15584824 targets/54383388 bytes, EOS161241 positions/9163 batches,1000 negative rollouts are saved.

## Decision and one next factor

Scientific-control primary Pareto=True; anchor Pareto=True. Strict gate=False. Human NLL guard passes but daily nonloop guard fails; overall practical guard=False. **Not adopted**; public/research adopted anchor remains unchanged. NLL gains and one technical sentence do not establish daily Japanese improvement.

Next proposed Round37: remove original standalone-newline CE only at the already eligible authentic human end positions, keep EOS coefficient0.3 and the original valid-target denominator. Original data/targets, prefix sampling, all other losses and all other conditions remain fixed, same aligned Round28 parent,10000 real updates. This isolates the competing target rather than another coefficient or data/size change. Evaluation retains original NL gold likelihood and all existing strict/practical guards; possible likelihood tradeoffs must be reported. This note alone does not claim Round37 started.

The previous boundary manifest records the historical a2439ad tree and pending reading at that moment; the final artifact-manifest.json supersedes it for the completed assessment. No new TEST or deployment.
