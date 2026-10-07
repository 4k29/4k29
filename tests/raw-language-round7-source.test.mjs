import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {gunzipSync} from 'node:zlib';
const root=path.resolve('training/language/round7');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const hash=p=>digest(fs.readFileSync(p));
const documents=fs.readFileSync(path.join(root,'mdn-documents.jsonl'),'utf8').trim().split('\n').map(JSON.parse);

test('new licensed prose is archived exactly and remains unassigned and untrained',()=>{
  const s=read(path.join(root,'mdn-sources.json'));
  assert.equal(s.documents,1457);assert.equal(documents.length,s.documents);
  assert.equal(s.characters,documents.reduce((n,d)=>n+[...d.text].length,0));
  assert.equal(s.utf8Bytes,documents.reduce((n,d)=>n+Buffer.byteLength(d.text),0));
  assert.equal(s.documentsSha256,hash(path.join(root,'mdn-documents.jsonl')));
  assert.equal(s.creditsSha256,hash(path.join(root,'mdn-credits.json')));
  assert.equal(s.partitionsNotAssigned,true);assert.equal(s.optimizerUpdates,0);assert.equal(s.tokenizerNotFitted,true);
  assert.equal(s.notUsedByRunningRound6,true);assert.equal(s.wikipedia,false);
  assert.equal(s.attemptFailureAndSkipDetailsNotRetained,true);assert.equal(s.failed,null);assert.equal(s.skipped,null);
  assert.equal(s.finalizedWithSeparateVerifier,true);assert.equal(s.sourceArchiveFilesVerified,1457);
  const archives=new Set(),ids=new Set();
  for(const d of documents) {
    assert.ok(!ids.has(d.id));ids.add(d.id);assert.equal(d.site,'mdn');assert.equal(d.author,'MDN contributors');
    assert.equal(d.license,'CC BY-SA 4.0');assert.ok(d.finalUrl.startsWith('https://developer.mozilla.org/ja/docs/'));
    assert.equal(d.discoveryOnlyCommitNotHtmlVersion,true);assert.equal(d.discoveryCommit,s.discoveryCommit);
    assert.equal(d.textSha256,digest(Buffer.from(d.text)));assert.equal(d.text,d.blocks.map(b=>b.text).join('\n'));
    assert.ok(d.blocks.every(b=>b.tag==='p'&&[...b.text].length>=40));
    const p=path.join(root,d.htmlArchive);archives.add(path.resolve(p));
    assert.equal(hash(p),d.htmlArchiveSha256);assert.equal(digest(gunzipSync(fs.readFileSync(p))),d.htmlSha256);
  }
  assert.equal(archives.size,1457);
  assert.deepEqual([...archives].sort(),fs.readdirSync(path.join(root,'source-html')).map(n=>path.join(root,'source-html',n)).sort());
  const credits=read(path.join(root,'mdn-credits.json'));assert.deepEqual(credits.map(d=>d.id),documents.map(d=>d.id));
  for(const d of credits) {assert.equal(Object.hasOwn(d,'text'),false);assert.equal(Object.hasOwn(d,'blocks'),false);}
});

test('executed collector, repaired metadata, parser and license snapshots retain distinct provenance',()=>{
  const s=read(path.join(root,'mdn-sources.json'));
  for(const [field,p] of [['executedCollectorSourceSha256','collector-executed-before-metadata-fix.py.txt'],['correctedCollectorSourceSha256','collect_mdn.py'],['verifierSourceSha256','verify_collected.py'],['copyrightPolicySha256','source-discovery/copyright-policy.html'],['robotsSha256','source-discovery/robots.txt']])assert.equal(s[field],hash(path.join(root,p)));
  assert.notEqual(s.executedCollectorSourceSha256,s.correctedCollectorSourceSha256);
  assert.equal(s.parserSourceSha256,hash(path.resolve('training/dialogue/collect_mdn_language.py')));
  assert.equal(s.baseCollectorSourceSha256,hash(path.resolve('training/language/collect_sources.py')));
  assert.equal(s.previousDocumentsSha256,hash(path.resolve('training/language/round3/documents.jsonl')));
  for(const key of ['externalWeights','externalTokenizer','externalInferenceAPI'])assert.equal(s[key],false);
  const terms=fs.readFileSync(path.join(root,'source-discovery/copyright-policy.html'),'utf8');
  assert.ok(terms.includes('creativecommons.org/licenses/by-sa/2.5/')&&terms.includes('any later version'));
  assert.equal(read(path.join(root,'source-discovery/commit-metadata.json')).sha,s.discoveryCommit);
  assert.equal(read(path.join(root,'source-discovery/ja-web-tree.json')).sha,s.discoveryTreeSha);
});

test('source inventory preserves every artifact and pre-split overlap audit',()=>{
  const m=read(path.join(root,'source-manifest.json'));
  for(const f of m.files) {
    const p=path.join(root,f.path);assert.equal(hash(p),f.sha256,f.path);assert.equal(fs.statSync(p).size,f.bytes);
    assert.ok(f.bytes<100*1024*1024);
  }
  assert.equal(m.optimizerUpdates,0);assert.equal(m.partitionsAssigned,false);assert.equal(m.tokenizerFitted,false);
  const o=read(path.join(root,'overlap-audit.json'));
  assert.equal(o.sourceDocumentsSha256,hash(path.join(root,'mdn-documents.jsonl')));
  assert.equal(o.priorDocumentsSha256,hash(path.resolve('training/language/round3/documents.jsonl')));
  assert.equal(o.priorSplitSha256,hash(path.resolve('training/language/round3/split.json')));
  assert.equal(o.auditorSourceSha256,hash(path.join(root,'audit_overlap.py')));
  assert.equal(o.newDocuments,1457);assert.equal(o.newDocumentsConnectedToPriorNonTrain,0);
  assert.equal(o.partitionsAssigned,false);assert.equal(o.tokenizerFitted,false);assert.equal(o.optimizerUpdates,0);
  assert.equal(o.groups.reduce((n,g)=>n+g.newDocuments.length,0),1457);
});
