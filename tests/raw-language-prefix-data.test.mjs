import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import zlib from 'node:zlib';
const root=path.resolve('training/language/round2');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');

test('prefix views preserve source bytes, true boundaries and held data',()=>{
  const dir=path.join(root,'prefix-bpe-8192');
  const original=path.join(root,'paragraph-bpe-8192');
  for(const f of ['tokenizer.json','validation.tokens.bin','validation.index.json','test.tokens.bin','test.index.json'])
    assert.deepEqual(fs.readFileSync(path.join(dir,f)),fs.readFileSync(path.join(original,f)),f);
  const docs=new Map(fs.readFileSync(path.join(root,'documents.jsonl'),'utf8').trim().split('\n').map(JSON.parse).map(d=>[d.id,d]));
  const parts=new Map(read(path.join(root,'split.json')).assignments.map(r=>[r.document,r.partition]));
  const cuts=read(path.join(dir,'prefix-cuts.json'));
  for(const c of cuts) {
    assert.equal(parts.get(c.document),'train');
    const text=docs.get(c.document).text.split(/\r?\n/)[c.line];
    assert.equal(hash(Buffer.from(text)),c.rawParagraphSha256);
    assert.equal(hash(Buffer.from(text.trim())),c.normalizedParagraphSha256);
    assert.ok(c.cutCharacters>=1&&c.cutCharacters<=Math.min([...text].length-1,96));
  }
  const index=read(path.join(dir,'train.index.json'));
  const buffer=fs.readFileSync(path.join(dir,'train.tokens.bin'));
  assert.equal(hash(buffer),index.tokensSha256);
  const bytes=read(path.join(dir,'tokenizer.json')).bytes;
  const units=index.documents.filter(u=>u.variant==='prefix-cut');
  assert.equal(units.length,cuts.length);
  let indented=0;
  for(let i=0;i<units.length;i+=Math.max(1,Math.floor(units.length/128))) {
    const u=units[i],ids=Array.from({length:u.length},(_,n)=>buffer.readUInt32LE((u.offset+n)*4));
    assert.equal(ids[0],1);assert.equal(ids.at(-1),2);
    assert.ok(!ids.slice(1,-1).some(t=>t<6),'no internal special tokens');
    const decoded=Buffer.concat(ids.slice(1,-1).map(t=>Buffer.from(bytes[t],'hex')));
    const originalText=docs.get(u.sourceDocument).text.split(/\r?\n/)[u.line];
    assert.deepEqual(decoded,Buffer.from(originalText));
    if(originalText.startsWith('　'))indented++;
  }
  assert.ok(indented>0,'original ideographic indentation is retained');
});

for(const folder of ['validation-5000','prefix-validation-5000'])test(`${folder} is an actual bound snapshot, not a completed run`,()=>{
  const dir=path.join(root,folder),snapshot=read(path.join(dir,'snapshot.json'));
  const packed=fs.readFileSync(path.join(dir,'model.js.gz'));
  assert.equal(hash(packed),snapshot.compressedModelSha256);
  assert.equal(hash(zlib.gunzipSync(packed)),snapshot.uncompressedModelSha256);
  assert.equal(snapshot.actualSavedUpdates,5000);
  assert.equal(snapshot.completedRequestedRun,false);
  assert.deepEqual(snapshot.optimizerStepCounters,[5000]);
  if(folder.startsWith('prefix-')) {
    assert.equal(snapshot.training.parentSelectedSteps,10000);
    assert.equal(snapshot.training.ownParentOnly,true);
    assert.equal(snapshot.training.optimizerReset,true);
  }
  const python=read(path.join(dir,'validation.json')),js=read(path.join(dir,'validation-js.json'));
  assert.equal(python.modelFileSha256,snapshot.compressedModelSha256);
  assert.equal(js.modelSha256,snapshot.uncompressedModelSha256);
  for(let i=0;i<python.rows.length;i++) {
    for(const k of ['id','text','tokens','eos','validUtf8','validTokens','inputTokens'])
      assert.deepEqual(js.rows[i][k],python.rows[i][k],k);
  }
});
