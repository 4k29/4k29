import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const root=path.resolve('training/language/round2');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const docs=fs.readFileSync(path.join(root,'documents.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
const split=read(path.join(root,'split.json'));
const parts=new Map(split.assignments.map(r=>[r.document,r.partition]));

test('new government editions never share a long paragraph across partitions',()=>{
  const seen=new Map();
  for(const d of docs.filter(d=>['mic','env'].includes(d.site))) for(const p of d.text.split('\n')) {
    if(p.length<80) continue;
    const h=hash(p);if(seen.has(h)) assert.equal(parts.get(d.id),seen.get(h));
    seen.set(h,parts.get(d.id));
  }
  const old=read(path.resolve('training/language/split.json'));
  for(const r of old.assignments) assert.equal(parts.get(r.document),r.partition);
});

test('fresh probes exclude previously reviewed documents and every training opening',()=>{
  const prior=read(path.resolve('training/language/generation-policy.json'));
  const consumed=new Set(Object.values(prior.probes).flat().map(r=>r.document));
  const policy=read(path.join(root,'generation-policy.json'));
  const train=docs.filter(d=>parts.get(d.id)==='train');
  for(const [part,rows] of Object.entries(policy.probes)) for(const row of rows) {
    assert.equal(parts.get(row.document),part);assert.ok(!consumed.has(row.document));
    assert.ok(!train.some(d=>d.text.includes(row.prefix)));
    const d=docs.find(d=>d.id===row.document);assert.ok(d.text.includes(row.referenceParagraph));
    assert.ok(row.referenceParagraph.startsWith(row.prefix));assert.equal(hash(d.text),row.textSha256);
  }
});

test('own new vocabularies fit only TRAIN and preserve exact merge-prefix comparison',()=>{
  const sample=read(path.join(root,'tokenizer-fit-sample.json'));
  for(const p of sample.paragraphs) {
    assert.equal(parts.get(p.document),'train');assert.equal(hash(p.text),p.sha256);
    assert.equal(docs.find(d=>d.id===p.document).text.split('\n')[p.line],p.text);
  }
  const a=read(path.join(root,'bpe-4096/tokenizer.json'));
  const b=read(path.join(root,'bpe-8192/tokenizer.json'));
  assert.deepEqual(a.merges,b.merges.slice(0,4096));assert.deepEqual(a.bytes,b.bytes.slice(0,4358));
  for(const d of docs) assert.equal(hash(d.text),d.textSha256);
});

test('all earlier frozen experiment files retain their recorded hashes',()=>{
  const previous=read(path.resolve('training/language/reproducibility-manifest.json'));
  for(const f of previous.files) assert.equal(hash(fs.readFileSync(path.resolve('training/language',f.path))),f.sha256,f.path);
});
