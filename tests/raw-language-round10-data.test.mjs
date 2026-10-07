import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createAdjacentBPE} from '../training/dialogue/bpe_heap.mjs';
const root=path.resolve('training/language/round10');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const units=read(path.join(root,'units.json'));
test('raw word experiment freezes source/data separately from active optimizer runs',()=>{
 const m=read(path.join(root,'source-manifest.json'));assert.equal(m.optimizerUpdatesInSnapshot,0);assert.equal(m.testGenerationOpened,false);
 for(const f of m.files){assert.equal(hash(path.join(root,f.path)),f.sha256,f.path);assert.equal(fs.statSync(path.join(root,f.path)).size,f.bytes);assert.ok(!f.path.includes('pilot-1000'));}
 const p=read(path.join(root,'training-policy.json'));
 for(const [f,k] of [['train.py','trainerSourceSha256'],['initialization.py','initializationSourceSha256'],['batching.py','batchingSourceSha256'],['word-experiment-policy.json','wordPolicySha256'],['generation-policy.json','generationPolicySha256']])assert.equal(hash(path.join(root,f)),p[k]);
 assert.equal(p.parentManifestSha256,hash(path.resolve('training/language/round8/reproducibility-manifest.json')));assert.equal(p.qaAllowed,false);
});
test('inherited folds and original units remain fixed; all probe prefixes absent from TRAIN',()=>{
 const parts=new Map(read(path.join(root,'split.json')).assignments.map(a=>[a.document,a.partition]));
 for(const a of read(path.resolve('training/language/round8/split.json')).assignments)assert.equal(parts.get(a.document),a.partition);
 const lookup=new Map(units.map(u=>[`${u.document}|${u.startLine}|${u.endLine}`,u]));
 for(const u of read(path.resolve('training/language/round8/units.json')))assert.deepEqual(lookup.get(`${u.document}|${u.startLine}|${u.endLine}`),u);
 const p=read(path.join(root,'generation-policy.json')),old=read(path.resolve('training/language/round8/generation-policy.json')),train=units.filter(u=>u.partition==='train').map(u=>u.text).join('\n');
 assert.equal(p.probes.validation.length,17);assert.equal(p.probes.test.length,34);
 for(const [part,probes] of Object.entries(p.probes)){assert.deepEqual(probes.slice(0,old.probes[part].length),old.probes[part]);for(const probe of probes)assert.equal(train.includes(probe.prefix),false);}
});
test('own word pieces roundtrip raw bytes and canonical JS tokenization matches saved Python streams',()=>{
 const base=read(path.join(root,'unicode-bpe-4681/tokenizer.json')),lookup=new Map(units.map(u=>[`${u.document}|${u.startLine}|${u.endLine}`,u]));
 for(const n of [512,1024]){
  const d=path.join(root,`word-bpe-${n}`),tok=read(path.join(d,'tokenizer.json')),encode=createAdjacentBPE(tok),meta=read(path.join(d,'data.json'));
  assert.equal(tok.wordMerges,n);assert.equal(meta.tokenizerSha256,hash(path.join(d,'tokenizer.json')));assert.equal(tok.bytes.length,4943+n);
  assert.deepEqual(tok.bytes.slice(0,base.bytes.length),base.bytes);assert.deepEqual(tok.merges.slice(0,base.merges.length),base.merges);
  for(const b of tok.bytes.slice(base.bytes.length)){const raw=Buffer.from(b,'hex');assert.ok(raw.length<=18);assert.deepEqual(Buffer.from(raw.toString('utf8')),raw);}
  for(const part of ['train','validation','test']){
   const idx=read(path.join(d,`${part}.index.json`)),raw=fs.readFileSync(path.join(d,`${part}.tokens.bin`));assert.equal(hash(path.join(d,`${part}.tokens.bin`)),idx.tokensSha256);
   assert.deepEqual([...new Set(idx.documents.map(d=>d.variant))],part==='train'?[0,1]:[0]);
   const canonical=idx.documents.filter(d=>d.variant===0);
   for(const doc of canonical.filter((_,i)=>i%Math.max(1,Math.floor(canonical.length/32))===0)){
    const u=lookup.get(`${doc.sourceDocument}|${doc.startLine}|${doc.endLine}`),ids=Array.from({length:doc.length},(_,i)=>raw.readUInt32LE((doc.offset+i)*4));assert.equal(u.partition,part);assert.equal(ids[0],1);assert.equal(ids.at(-1),2);
    assert.deepEqual(ids.slice(1,-1),encode(u.text));assert.deepEqual(Buffer.concat(ids.slice(1,-1).map(t=>Buffer.from(tok.bytes[t],'hex'))),Buffer.from(u.text));
    const chars=[...u.text];for(const cut of [1,5,16]){const prefix=chars.slice(0,cut).join(''),tokens=encode(prefix);assert.deepEqual(Buffer.concat(tokens.map(t=>Buffer.from(tok.bytes[t],'hex'))),Buffer.from(prefix));}
   }
  }
 }
});
