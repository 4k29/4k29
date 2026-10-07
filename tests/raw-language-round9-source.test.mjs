import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import {execFileSync} from 'node:child_process';
const root=path.resolve('training/language/round9-source');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const hash=p=>digest(fs.readFileSync(p));
const docs=fs.readFileSync(path.join(root,'documents.jsonl'),'utf8').trim().split('\n').map(JSON.parse);

test('government source snapshot records attributable original bytes and zero training',()=>{
 const m=read(path.join(root,'sources.json')),credits=new Map(m.sources.map(s=>[s.id,s]));
 assert.equal(docs.length,287);assert.equal(m.documents,287);assert.equal(m.actualOptimizerUpdates,0);assert.equal(m.tokenizerTraining,false);
 assert.equal(m.characters,docs.reduce((n,d)=>n+[...d.text].length,0));assert.equal(m.utf8Bytes,docs.reduce((n,d)=>n+Buffer.byteLength(d.text),0));
 assert.equal(m.collectorSourceSha256,hash(path.join(root,'collect.py')));assert.equal(m.policySnapshotSha256,hash(path.join(root,'source-policy/index.json')));
 assert.equal(new Set(docs.map(d=>d.url)).size,287);assert.equal(new Set(docs.map(d=>d.textSha256)).size,287);
 for(const d of docs){
  const s=credits.get(d.id),html=gunzipSync(fs.readFileSync(path.join(root,d.htmlArchive)));
  assert.equal(d.partition,undefined);assert.equal(digest(html),d.htmlSha256);assert.equal(d.htmlSha256,s.htmlSha256);
  assert.equal(digest(Buffer.from(d.text)),d.textSha256);assert.equal(d.textSha256,s.textSha256);assert.equal(s.licenseUrl,'https://creativecommons.org/licenses/by/4.0/');assert.ok(s.attribution.includes(d.url));
  assert.equal(d.blocks.map(b=>b.text).join('\n'),d.text);assert.ok(d.blocks.every(b=>b.tag==='p'&&[...b.text].length>=40));
 }
 assert.equal(read(path.join(root,'attempts.json')).allFailuresAndSkipsRetained,true);
});

test('saved official source policies and every archive pass original parser verification',()=>{
 const p=read(path.join(root,'source-policy/index.json'));for(const f of p.files)assert.equal(hash(path.join(root,f.path)),f.sha256);
 assert.equal(p.robots.stat.status,200);assert.equal(p.robots.bunka.status,404);
 assert.match(fs.readFileSync(path.join(root,'source-policy/mext-terms.html'),'utf8'),/bunka\.go\.jp/);
 const before=hash(path.join(root,'verification.json'));
 execFileSync('python3',[path.join(root,'verify.py')],{encoding:'utf8'});
 assert.equal(hash(path.join(root,'verification.json')),before);
 execFileSync('python3',[path.join(root,'test_discovery.py')],{stdio:'pipe'});
 const v=read(path.join(root,'verification.json'));assert.equal(v.allArchivesReparsed,true);assert.equal(v.wholeOriginalParagraphsVerified,true);assert.equal(v.verificationSourceSha256,hash(path.join(root,'verify.py')));
});

test('source inventory and overlap audit remain bound to the frozen round8 fold',()=>{
 const inventory=read(path.join(root,'source-manifest.json'));assert.equal(inventory.files.length,310);
 for(const f of inventory.files){const file=path.join(root,f.path);assert.equal(hash(file),f.sha256,f.path);assert.equal(fs.statSync(file).size,f.bytes);}
 const overlap=read(path.join(root,'overlap-audit.json'));assert.equal(overlap.optimizerUpdates,0);assert.equal(overlap.partitionsAssigned,false);assert.equal(overlap.tokenizerFitted,false);
 assert.equal(overlap.priorDocumentsSha256,hash(path.resolve('training/language/round8/documents.jsonl')));assert.equal(overlap.priorSplitSha256,hash(path.resolve('training/language/round8/split.json')));assert.equal(overlap.sourceDocumentsSha256,hash(path.join(root,'documents.jsonl')));assert.equal(overlap.auditorSourceSha256,hash(path.join(root,'audit_overlap.py')));
 assert.equal(overlap.newDocumentsConnectedToPriorNonTrain,0);assert.equal(overlap.newDocuments,287);assert.equal(overlap.groupsWithNewDocuments,258);
 assert.notEqual(hash(path.join(root,'collect.py')),hash(path.join(root,'collector-v1-before-link-fix.py.txt')));
});
