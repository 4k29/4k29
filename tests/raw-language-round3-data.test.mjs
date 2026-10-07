import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const root=path.resolve('training/language/round3');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const docs=fs.readFileSync(path.join(root,'documents.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
const byId=new Map(docs.map(d=>[d.id,d]));
const split=read(path.join(root,'split.json'));
const parts=new Map(split.assignments.map(d=>[d.document,d.partition]));
const units=read(path.join(root,'units.json'));

test('all exact long paragraph groups remain in one partition, including quarantine',()=>{
  const seen=new Map();
  for(const d of docs)for(const p of d.text.split('\n')) {
    if(p.trim().length<80)continue;
    const key=hash(p.trim());if(seen.has(key))assert.equal(parts.get(d.id),seen.get(key));
    seen.set(key,parts.get(d.id));
  }
  const prior=read(path.resolve('training/language/round2/split.json'));
  for(const d of prior.assignments)if(d.partition!=='train')assert.ok(['development','quarantine'].includes(parts.get(d.document)));
  assert.equal(split.previousWeightsNotAllowed,true);
});

test('raw chains preserve exact contiguous source bytes and short quotations',()=>{
  let short=0;
  for(const u of units) {
    const raw=byId.get(u.document).text.split('\n').slice(u.startLine,u.endLine).join('\n');
    assert.equal(u.text,raw);assert.equal(hash(raw),u.textSha256);
    assert.equal(parts.get(u.document),u.partition);
    assert.equal((raw.match(/「/g)||[]).length,(raw.match(/」/g)||[]).length);
    for(const p of raw.split('\n'))if(p.trim().length<40&&p.includes('「')&&p.trim().endsWith('」'))short++;
  }
  assert.ok(short>3000);
  for(const size of [4096,8192]) {
    const dir=path.join(root,`raw-bpe-${size}`),vocab=read(path.join(dir,'tokenizer.json')).bytes;
    for(const part of ['train','validation','test']) {
      const index=read(path.join(dir,`${part}.index.json`)),bytes=fs.readFileSync(path.join(dir,`${part}.tokens.bin`));
      assert.equal(hash(bytes),index.tokensSha256);
      for(let i=0;i<index.documents.length;i+=Math.max(1,Math.floor(index.documents.length/64))) {
        const u=index.documents[i],ids=Array.from({length:u.length},(_,n)=>bytes.readUInt32LE((u.offset+n)*4));
        assert.equal(ids[0],1);assert.equal(ids.at(-1),2);assert.ok(ids.slice(1,-1).every(t=>t>=6));
        const text=Buffer.concat(ids.slice(1,-1).map(t=>Buffer.from(vocab[t],'hex')));
        const original=byId.get(u.sourceDocument).text.split('\n').slice(u.startLine,u.endLine).join('\n');
        assert.deepEqual(text,Buffer.from(original));
      }
    }
  }
});

test('new raw vocabulary and probes exclude all current held text and reviewed documents',()=>{
  const sample=read(path.join(root,'tokenizer-fit-sample.json'));
  for(const u of sample.units)assert.equal(parts.get(u.document),'train');
  const consumed=new Set(['training/language/generation-policy.json','training/language/round2/generation-policy.json'].flatMap(p=>Object.values(read(p).probes).flat().map(d=>d.document)));
  const train=docs.filter(d=>parts.get(d.id)==='train');
  for(const [part,probes] of Object.entries(read(path.join(root,'generation-policy.json')).probes))for(const p of probes) {
    assert.equal(parts.get(p.document),part);assert.ok(!consumed.has(p.document));
    assert.ok(!train.some(d=>d.text.includes(p.prefix)));
    assert.ok(byId.get(p.document).text.includes(p.referenceParagraph));
  }
  const small=read(path.join(root,'raw-bpe-4096/tokenizer.json')),large=read(path.join(root,'raw-bpe-8192/tokenizer.json'));
  assert.deepEqual(small.merges,large.merges.slice(0,4096));assert.deepEqual(small.bytes,large.bytes.slice(0,4358));
});

test('all frozen round2 artifacts and shared implementations remain byte-identical',()=>{
  const previousRoot=path.resolve('training/language/round2'),manifest=read(path.join(previousRoot,'reproducibility-manifest.json'));
  for(const f of manifest.files)assert.equal(hash(fs.readFileSync(path.join(previousRoot,f.path))),f.sha256,f.path);
  for(const f of manifest.sharedFiles)assert.equal(hash(fs.readFileSync(path.resolve(f.path))),f.sha256,f.path);
});
