import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
const root=path.resolve('training/language/round11');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
test('multiview preparation binds original source and vocabulary before learning, without TEST encoding',()=>{
  const manifest=read(path.join(root,'source-manifest.json'));
  assert.equal(manifest.completedUpdatesAtSourceFreeze,0);
  for(const row of manifest.files){
    const p=path.join(root,row.path);
    assert.equal(fs.statSync(p).size,row.bytes,row.path);
    assert.equal(sha(p),row.sha256,row.path);
  }
  const policy=read(path.join(root,'policy.json'));
  for(const [name,hash] of Object.entries(policy.sourceHashes))assert.equal(sha(path.join(root,'../round10',name)),hash,name);
  for(const [name,hash] of Object.entries(policy.codeHashes))assert.equal(sha(path.join(root,name)),hash,name);
  assert.equal(sha(path.join(root,'../round10/reproducibility-manifest.json')),policy.parentManifestSha256);
  assert.equal(sha(path.join(root,'multiview/tokenizer.json')),policy.sourceHashes['word-bpe-512/tokenizer.json']);
  assert.equal(fs.existsSync(path.join(root,'multiview/test.tokens.bin')),false);
  const data=read(path.join(root,'multiview/data.json'));
  assert.equal(data.policySha256,sha(path.join(root,'policy.json')));
  for(const part of ['train','validation']){
    const index=read(path.join(root,'multiview',part+'.index.json'));
    assert.equal(sha(path.join(root,'multiview',part+'.tokens.bin')),index.tokensSha256);
    const stats=data.stats[part];
    for(const key of ['units','utf8Bytes'])assert.equal(stats['0'][key],stats['1'][key]),assert.equal(stats['0'][key],stats['2'][key]);
  }
});
