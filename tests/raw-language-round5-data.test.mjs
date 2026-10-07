import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createAdjacentBPE} from '../training/dialogue/bpe_heap.mjs';
const root=path.resolve('training/language/round5'),parent=path.resolve('training/language/round3');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const meta=read(path.join(root,'preparation.json')),dir=path.join(root,`unicode-bpe-${meta.merges}`);
const tok=read(path.join(dir,'tokenizer.json')),encode=createAdjacentBPE(tok);
const units=read(path.join(parent,'units.json'));

test('character vocabulary is observed only in TRAIN and assembles single Unicode glyphs',()=>{
  const counts=new Map();for(const u of units.filter(u=>u.partition==='train'))for(const c of u.text)counts.set(c,(counts.get(c)||0)+1);
  const freq=read(path.join(root,'character-frequencies.json'));
  assert.equal(freq.length,4259);assert.equal(tok.bytes.length,4765);assert.equal(tok.wordMerges,0);
  assert.equal(meta.preparerSourceSha256,hash(path.join(root,'prepare_characters.py')));
  assert.equal(meta.tokenizerSha256,hash(path.join(dir,'tokenizer.json')));
  for(const r of freq) {
    assert.equal(r.frequency,counts.get(r.character));assert.deepEqual(encode(r.character),[r.token]);
    assert.equal(Buffer.from(tok.bytes[r.token],'hex').toString('utf8'),r.character);
    assert.equal([...r.character].length,1);
  }
  for(const u of units.filter((_,i)=>i%Math.max(1,Math.floor(units.length/32))===0)) {
    const characters=[...u.text],encoded=encode(u.text);
    for(const cut of [1,32,80].map(n=>Math.min(n,characters.length-1))) {
      assert.deepEqual([...encode(characters.slice(0,cut).join('')),...encode(characters.slice(cut).join(''))],encoded);
    }
  }
});

test('new streams preserve contiguous original bytes and true source boundaries',()=>{
  const lookup=new Map(units.map(u=>[`${u.document}|${u.startLine}|${u.endLine}`,u]));
  for(const part of ['train','validation','test']) {
    const idx=read(path.join(dir,`${part}.index.json`)),bytes=fs.readFileSync(path.join(dir,`${part}.tokens.bin`));
    assert.equal(idx.tokensSha256,hash(path.join(dir,`${part}.tokens.bin`)));
    for(const d of idx.documents.filter((_,i)=>i%Math.max(1,Math.floor(idx.documents.length/64))===0)) {
      const u=lookup.get(`${d.sourceDocument}|${d.startLine}|${d.endLine}`);
      assert.equal(u.partition,part);const ids=Array.from({length:d.length},(_,n)=>bytes.readUInt32LE((d.offset+n)*4));
      assert.equal(ids[0],1);assert.equal(ids.at(-1),2);assert.ok(ids.slice(1,-1).every(t=>t>=6));
      assert.deepEqual(Buffer.concat(ids.slice(1,-1).map(t=>Buffer.from(tok.bytes[t],'hex'))),Buffer.from(u.text));
      if(part==='train')assert.equal(ids.length-2,[...u.text].length);
    }
  }
  const policy=read(path.join(root,'generation-policy.json')),old=read(path.join(parent,'generation-policy.json'));
  assert.deepEqual(policy.probes,old.probes);assert.deepEqual(policy.acceptance,old.acceptance);
  assert.equal(policy.generation.maxNewTokens,192);
});

test('all frozen raw parent experiments and shared implementations stay unchanged',()=>{
  for(const name of ['round3','round4']) {
    const base=path.resolve('training/language',name),m=read(path.join(base,'reproducibility-manifest.json'));
    for(const f of m.files)assert.equal(hash(path.join(base,f.path)),f.sha256,f.path);
    for(const f of m.sharedFiles)assert.equal(hash(path.resolve(f.path)),f.sha256,f.path);
  }
});
