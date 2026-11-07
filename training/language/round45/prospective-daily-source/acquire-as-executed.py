"""Acquire pinned human chat only; preserve speaker-disjoint prospective folds.
No tokenization, model execution, or use by the running Round26.
"""
import collections, hashlib, io, json, pathlib, urllib.request, zipfile
BASE = pathlib.Path('/workspace/daily-conversation-source-audit')
fold_record = json.loads((BASE / 'prospective-speaker-folds.json').read_text())
repo = fold_record['sourceRepository']; commit = fold_record['sourceCommit']
folds = fold_record['speakerFolds']
tree = json.loads((BASE / 'real-persona-chat-tree.json').read_text())['tree']
expected = {x['path']: x for x in tree if x['path'].startswith('real_persona_chat/dialogues/') and x['path'].endswith('.json')}
url = f'https://codeload.github.com/{repo}/zip/{commit}'
with urllib.request.urlopen(url, timeout=45) as response:
    archive_bytes = response.read(128 * 1024 * 1024 + 1)
assert len(archive_bytes) <= 128 * 1024 * 1024
out = BASE / 'human-only-raw'
out.mkdir(exist_ok=True)
records = []; counts = collections.Counter(); seen = set()
with zipfile.ZipFile(io.BytesIO(archive_bytes)) as z:
    for item in z.infolist():
        rel = item.filename.split('/', 1)[1] if '/' in item.filename else ''
        if rel not in expected:
            continue  # Never extract/parse the separate LLM-log directory or speaker profiles.
        assert rel not in seen; seen.add(rel)
        raw = z.read(item)
        git_sha = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        assert git_sha == expected[rel]['sha']
        data = json.loads(raw)
        speakers = data['interlocutors']
        assert len(speakers) == 2 and len(set(speakers)) == 2
        group = {folds[s] for s in speakers}
        fold = next(iter(group)) if len(group) == 1 else 'excluded-cross-speaker-fold'
        if data['dialogue_id'] == 1:
            fold = 'excluded-public-readme-example'
        counts[fold] += 1
        # Read only metadata for allocation; never inspect/encode held-out utterances.
        target = out / fold / pathlib.PurePosixPath(rel).name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(raw)
        records.append(dict(dialogueId=data['dialogue_id'], sourcePath=rel, speakers=speakers, fold=fold, gitBlobSha1=git_sha, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw)))
assert seen == set(expected)
(out / 'LICENSE').write_bytes((BASE / 'real-persona-chat-LICENSE').read_bytes())
manifest = dict(sourceRepository=repo, sourceCommit=commit, archiveUrl=url, downloadedArchiveSha256=hashlib.sha256(archive_bytes).hexdigest(), license='CC-BY-SA-4.0', attribution='Sanae Yamashita et al., RealPersonaChat (PACLIC 2023), nu-dialogue/real-persona-chat', paper='https://aclanthology.org/2023.paclic-1.85/', foldPolicySha256=hashlib.sha256((BASE / 'prospective-speaker-folds.json').read_bytes()).hexdigest(), acquisitionScriptSha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(), dialogueCounts=dict(counts), totalHumanDialogues=len(records), noLlmLogsExtractedOrParsed=True, speakerProfileFieldsNotExtracted=True, heldoutUtterancesNotInspectedOrEncoded=True, modelTrainingUpdates=0, usedByRound26=False, prospectiveSourceOnly=True, records=records)
(BASE / 'human-source-acquisition.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({k:v for k,v in manifest.items() if k!='records'}), flush=True)
