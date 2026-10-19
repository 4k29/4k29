# Separate authorized experiments

R25 executes only self-generated repetition-negative loss addition against R24. R26 will independently test new human original corpus mixture (0→10%), holding the adopted objective/model/config fixed. R27 will independently test only FFN hidden768→1536 (own random new features, zero output, exact old weights/moments). Each condition uses a full10000actual optimizer updates; no within-round switching. Repeats of a candidate also get separate rounds.

Adoption follows immutable ../round24/next-candidate-drafts/adoption-policy.json: same strict full-language gates, no public promotion, conservative count/CE Pareto evidence with explicit uncertainty and raw repetition diagnostics. If a candidate fails, retain the last adopted experimental baseline rather than carrying the failed change into the next factor. Scientific control is labeled independently of Git PR base. All are siblings of aligned ownRound11 latest unless explicitly registered otherwise; do not claim cumulative30000weight lineage.

Final human-prose data/rights/attribution/raw snapshots were prepared under ../round24/next-candidate-drafts/wiki-addition/source-cache/quality-sources but are NOT used by R25. Capacity prototypes/chunked storage also are NOT used by R25. Their prior synthetic/zero-update tests are not completed experimental rounds.
