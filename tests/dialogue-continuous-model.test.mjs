import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {dialogueModel} from '../training/dialogue/continuous-candidate.js';
import {createDialogueDecoder} from '../training/dialogue/inference.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL('../training/dialogue/'+name,import.meta.url)));
const decoder=createDialogueDecoder(dialogueModel);

test('continuous experiment is an own random model with 3000 raw and 10000 dialogue updates',()=>{
 const training=dialogueModel.training;
 assert.equal(training.randomInitialization,true);assert.equal(training.initializationKind,'random');
 assert.equal(training.externalWeights,false);assert.equal(training.externalInferenceAPIs,false);assert.equal(training.teacher,false);
 assert.equal(training.ownPretrainingParent,null);assert.equal(training.inheritedOwnPretrainingUpdates,0);
 assert.equal(training.completedSteps,13000);assert.equal(training.pretrainingUpdates,3000);assert.equal(training.dialogueUpdates,10000);
 assert.equal(training.parameters,609520);assert.equal(dialogueModel.config.context,256);assert.equal(dialogueModel.config.dim,128);
 assert.equal(training.settings.semantic_weight,0.3);assert.equal(training.settings.replay_weight,0.15);
 assert.equal(training.sourceSha256,read('continuous-corpus.json').sourceSha256);
 assert.equal(Object.values(dialogueModel.tensors).reduce((n,v)=>n+v.data.length,0),training.parameters);
});

test('semantic training heads do not participate in continuous model inference',()=>{
 const config={...dialogueModel.config};delete config.semanticTasks;
 const tensors=Object.fromEntries(Object.entries(dialogueModel.tensors).filter(([name])=>!name.startsWith('semantic.')));
 const withoutHeads=createDialogueDecoder({...dialogueModel,config,tensors});
 for(const question of ['MERは？','CMF BudsのANCは？','Headphone 1の重さは？']){
  const prefix=decoder.tokenizer.prompt(question);
  assert.deepEqual(decoder.logits(prefix),withoutHeads.logits(prefix));
  assert.deepEqual(decoder.generate(question),withoutHeads.generate(question));
 }
});

for(const [i,row] of read('continuous-reference.json').references.entries())test('continuous independent JavaScript matches PyTorch logits '+i,()=>{
 const actual=decoder.logits(row.tokens);
 assert.ok(Math.max(...actual.map((v,j)=>Math.abs(v-row.logits[j])))<0.0002);
});

test('continuous development generation matches independently implemented Python on every row',()=>{
 const python=read('continuous-test-results.json'),js=read('continuous-js-results.json');
 assert.equal(python.total,858);assert.equal(python.total,js.total);assert.equal(python.exact,js.exact);assert.equal(python.version,js.version);
 const byId=new Map(python.rows.map(r=>[r.id,r]));
 for(const row of js.rows){const expected=byId.get(row.id);assert.equal(row.answer,expected.answer);assert.equal(row.eos,expected.eos);assert.equal(row.validTokens,expected.validTokens);}
});

test('the independent JavaScript audit agrees on long histories and context budgets',()=>{
 const python=read('continuous-audit-results.json'),js=read('continuous-audit-js-results.json');
 assert.equal(python.total,100);assert.equal(python.total,js.total);assert.equal(python.exact,js.exact);
 const byId=new Map(python.rows.map(r=>[r.id,r]));
 for(const row of js.rows){const expected=byId.get(row.id);assert.equal(row.answer,expected.answer);assert.equal(row.eos,expected.eos);assert.equal(row.validTokens,expected.validTokens);}
});
