# Interim inference diagnostic — not a completed round

Live checkpoint was read after6,200 actual updates; best-by-fixed-DEV weights were from6,000. Training kept running. This directory contains an inference-only raw FP32 selected state and its standard7-decimal export. It does not contain optimizer/RNG and must not be used to resume. Resume only the current continue-10000/checkpoint.pt.

The old control is completedR25 selected9500, so this partial diagnostic does not replace the final equal-requested-update comparison. All12old/new daily prefixes and complete continuations were actually read; reading.json stores individual reasons and artifactSHA, FULL_GENERATIONS.md retains unedited text. Whole coherent continuations0→0; long loops11→12; EOS1→0. No supplementary gate or public adoption is invented. InterimJS/raw-vs-rounding checks are explicitly pending; final selected export receives the full planned numerical checks.

On the same99authentic humanDEV targets, canonical fixed-block NLL/serializedUTF8 byte is1.2880010131269757→1.2731152031613315. All source/target/window identities match. Lower loss has not produced meaningful daily continuations here. This is exposedDEV, not newTEST. The final selected model may differ and is still unassessed.

Reproduce inference with execution/evaluate_daily.py and execution/daily_human_likelihood.py pointing --model to this model.js and --out to a new file. Own tokenization and raw generation are reused; original training conditions and language gate are unchanged. run-diagnostics.py records the commands actually executed; snapshot.json binds raw selected state/model export/source checkpoint SHA. No optimizer updates are performed by these helpers.
