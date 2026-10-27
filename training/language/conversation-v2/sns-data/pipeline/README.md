# Permitted human conversation acquisition and processing

No live social-media posts are fetched. MRMPC is a published, selected and masked research text-chat corpus; OASST2 is human-crowdsourced assistant-role writing, not an SNS sample. Read rights/ before acquisition. Published source flags are not perfect human-authorship or privacy certification.

From repository root (Python standard library, existing own BPE only):

```
python training/language/conversation-v2/sns-data/pipeline/acquire_mrmpc.py
python training/language/conversation-v2/sns-data/pipeline/verify_source_blobs.py
python training/language/conversation-v2/sns-data/pipeline/privacy_prepare.py mrmpc
python training/language/conversation-v2/sns-data/pipeline/build.py
python training/language/conversation-v2/sns-data/pipeline/acquire_oasst.py
python training/language/conversation-v2/sns-data/pipeline/privacy_prepare.py oasst2
python training/language/conversation-v2/sns-data/pipeline/build_oasst.py
python training/language/conversation-v2/sns-data/pipeline/audit_overlap.py
python -m unittest discover -s training/language/conversation-v2/sns-data/pipeline -p 'test_*.py'
```

**Privacy preparation is mandatory before public packaging.** Acquirers first materialize source candidates; never add those unreviewed files to Git. The public pack withholds whole PII-flagged conversations/trees and the independently identified third-party translated-quotation tree. After manual reading exposed sensitive personal-health discussion missed by contact regexes, `publication-policy.json` was frozen before execution; its conservative sensitive-topic rule applies identically to both sources and withholds general health/financial discussion too. This is public-data minimization, not a claim about personal attributes or a TRAIN optimization. Unredacted candidates are temporary RAM-backed files under `/dev/shm/sns-private`, not repository artifacts. Reproduction may re-obtain material no longer available or subject to a new refusal; rights/opt-out decisions take precedence over old hashes. Do not upload quarantine.

Final public pack: MRMPC751 body conversations/78,811utterances (209 of960 acquired chats have metadata-only tombstones); OASST602 of788 acquired original Japanese rows, forming282 maximal branches/510unique messages after eligibility and ancestry checks (16 source trees/186rows withheld). No final model-training admissions. Counts remain candidate-only.

MRMPC: official pinned raw JSON only; pilot8, max2request starts/sec/concurrency2, 960 dialogue files, no interlocutor demographics/personality/profile file. Future runs abort queued work on HTTP failure, honor failure rather than bypass limits. All960 cached originals independently match official pinned Git blob identity. Metadata-only tombstones remain for withheld chats. Exact/verified-near conversation connections and source-local author/family connections are unioned before deterministic split. All source utterances remain in original order; no claim that the chronological predecessor or mention addressee is the exact reply parent. Three-person chats are ineligible for existing two-human-role serialization. Context fit numbers are budget diagnostics, not authorization to conflate speakers.

OASST2: one official pinned ready archive (54.3MB temporary RAM) is parsed, with only originally Japanese rows retained. Synthetic must explicitly be false, model_name empty, deleted false and review_result true. Complete source-parent ancestry must satisfy all conditions. No translations or generated reference answers. Branches ending in an assistant message retain full ancestry; short prefix paths are removed. Shared ancestors count once in unique-data volume, although serialized training exposure would repeat them. Source writers are separately pseudonymized; source semantic roles prompter/assistant are not persistent humanA/B identities. All shared writers, source trees and nontrivial exact text connect before split. The resulting giant component means this is not an independent in-source TRAIN/DEV benchmark.

No normalization/paraphrasing of text; NFC/whitespace canonicalization is used for overlap hashes only. No false EOS or fabricated speaker/parent. No training/tokenizer fit/weights changes. Automated Japanese, acknowledgement, content, PII and advertising indicators are review proxies, not judgments of semantic quality or legal rights. All final model-training admissions remain zero pending independent quality, source, serialization and evaluation gates.
