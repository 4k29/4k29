import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {dialogueModel} from '../training/dialogue/binding-candidate.js';
import {createDialogueDecoder} from '../training/dialogue/inference.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL('../training/dialogue/'+name,import.meta.url)));
const decoder=createDialogueDecoder(dialogueModel);
test('binding experiment uses random own weights and really completes 1000+10000 updates',()=>{
 const t=dialogueModel.training;
 assert.equal(t.randomInitialization,true);assert.equal(t.initializationKind,'random');assert.equal(t.externalWeights,false);assert.equal(t.externalInferenceAPIs,false);assert.equal(t.teacher,false);
 assert.equal(t.completedSteps,11000);assert.equal(t.pretrainingUpdates,1000);assert.equal(t.dialogueUpdates,10000);
 assert.equal(t.parameters,368630);assert.equal(t.settings.semantic_weight,0.3);assert.equal(t.settings.replay_weight,0.15);
 assert.equal(t.sourceSha256,read('binding-corpus.json').sourceSha256);
 assert.equal(Object.values(dialogueModel.tensors).reduce((n,v)=>n+v.data.length,0),t.parameters);
});
test('removing training-only semantic heads leaves identical independent inference',()=>{
 const config={...dialogueModel.config};delete config.semanticTasks;
 const tensors=Object.fromEntries(Object.entries(dialogueModel.tensors).filter(([name])=>!name.startsWith('semantic.')));
 const withoutHeads=createDialogueDecoder({...dialogueModel,config,tensors});
 for(const question of ['MERは？','CMF BudsのANCは？','Headphone 1の重さは？']){
  const prefix=decoder.tokenizer.prompt(question);
  assert.deepEqual(decoder.logits(prefix),withoutHeads.logits(prefix));
  assert.deepEqual(decoder.generate(question),withoutHeads.generate(question));
 }
});
for(const [i,row] of read('binding-reference.json').references.entries())test('binding independent JavaScript matches PyTorch logits '+i,()=>{
 const actual=decoder.logits(row.tokens);assert.ok(Math.max(...actual.map((v,j)=>Math.abs(v-row.logits[j])))<0.0002);
});
test('all binding development answers match between independently implemented runtimes',()=>{
 const python=read('binding-test-results.json'),js=read('binding-js-results.json');
 assert.equal(python.total,js.total);assert.equal(python.exact,js.exact);assert.equal(python.version,js.version);
 const byId=new Map(python.rows.map(r=>[r.id,r]));
 for(const row of js.rows){const expected=byId.get(row.id);assert.equal(row.answer,expected.answer);assert.equal(row.eos,expected.eos);assert.equal(row.validTokens,expected.validTokens);}
});
