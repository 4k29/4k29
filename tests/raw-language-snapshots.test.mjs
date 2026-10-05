import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
const root=new URL('../training/language/',import.meta.url),read=p=>JSON.parse(fs.readFileSync(new URL(p,root))),hash=b=>createHash('sha256').update(b).digest('hex');
test('all raw validation diagnostic snapshots retain exactly the exported weights and real partial-run counts',()=>{
 for(const [run,step] of [['raw-million',1000],['raw-million',5000],['paragraph-million',3000],['paragraph-million',5000]]){
  const prefix=`${run}/validation-${step}`,snapshot=read(prefix+'-snapshot.json'),generation=read(prefix+'.json'),manual=read(prefix+'-manual-review.json'),review=read(prefix+'-review.json'),compressed=fs.readFileSync(new URL(prefix+'-model.js.gz',root));
  assert.equal(snapshot.diagnosticOnly,true);assert.equal(hash(compressed),snapshot.compressedFileSha256||snapshot.compressedModelSha256);assert.equal(hash(gunzipSync(compressed)),snapshot.modelExportSha256||snapshot.modelSha256);assert.equal(generation.modelFileSha256,snapshot.modelExportSha256||snapshot.modelSha256);
  assert.equal(generation.partition,'validation');assert.equal(generation.training.completedRun,false);assert.equal(generation.training.completedSteps,step);assert.equal(generation.training.bestStep,snapshot.selectedStep||snapshot.selectedUpdates);assert.equal(generation.training.externalWeights,false);assert.equal(generation.rows.length,9);
  assert.equal(manual.generationSha256,hash(fs.readFileSync(new URL(prefix+'.json',root))));assert.equal(review.generationSha256,manual.generationSha256);assert.equal(review.total,9);assert.equal(review.independentHumanEvaluation,false);
 }
});
