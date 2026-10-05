import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {dialogueModel} from '../training/dialogue/switch-candidate.js';
import {createDialogueDecoder} from '../training/dialogue/inference.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL('../training/dialogue/'+name,import.meta.url)));
const decoder=createDialogueDecoder(dialogueModel);

test('topic-switch experiment completes 1000+10000 updates from own random initialization',()=>{
 const t=dialogueModel.training,selection=read('switch-validation-selection.json');
 assert.equal(t.completedSteps,11000);assert.equal(t.pretrainingUpdates,1000);assert.equal(t.dialogueUpdates,10000);
 assert.equal(t.randomInitialization,true);assert.equal(t.initializationKind,'random');assert.equal(t.ownPretrainingParent,null);
 assert.equal(t.externalWeights,false);assert.equal(t.externalInferenceAPIs,false);assert.equal(t.teacher,false);
 assert.equal(t.parameters,609778);assert.equal(dialogueModel.config.dim,128);assert.equal(dialogueModel.config.context,256);
 assert.equal(dialogueModel.config.vocabulary,1286);assert.equal(t.settings.answer_prefix_weight,1);
 assert.equal(t.sourceSha256,read('switch-corpus.json').sourceSha256);
 assert.equal(t.trainRows,21721);assert.equal(t.validationRows,512);assert.equal(t.fullValidationRows,2776);
 assert.equal(t.validationSelectionSha256,selection.idsSha256);
 assert.equal(Object.values(dialogueModel.tensors).reduce((n,v)=>n+v.data.length,0),609778);
});

test('topic-switch training heads do not supply or alter generated answers',()=>{
 const config={...dialogueModel.config};delete config.semanticTasks;
 const tensors=Object.fromEntries(Object.entries(dialogueModel.tensors).filter(([name])=>!name.startsWith('semantic.')));
 const plain=createDialogueDecoder({...dialogueModel,config,tensors});
 for(const q of ['MERは？','Headphone1の重量は？','Stringとは？']){
  assert.deepEqual(decoder.logits(decoder.tokenizer.prompt(q)),plain.logits(plain.tokenizer.prompt(q)));
  assert.deepEqual(decoder.generate(q),plain.generate(q));
 }
});

for(const [i,row] of read('switch-reference.json').references.entries())test('topic-switch independent logits match PyTorch '+i,()=>{
 const actual=decoder.logits(row.tokens);
 assert.ok(Math.max(...actual.map((v,j)=>Math.abs(v-row.logits[j])))<0.0002);
});

for(const [pythonFile,jsFile,total] of [['switch-test-results.json','switch-js-results.json',2818],['switch-audit-results.json','switch-audit-js-results.json',120]])test('topic-switch greedy generation agrees across independent runtimes '+pythonFile,()=>{
 const python=read(pythonFile),js=read(jsFile);
 assert.equal(python.total,total);assert.equal(js.total,total);assert.equal(python.exact,js.exact);
 const byId=new Map(python.rows.map(r=>[r.id,r]));
 for(const row of js.rows){
  const expected=byId.get(row.id);assert.equal(row.answer,expected.answer);
  assert.equal(row.eos,expected.eos);assert.equal(row.validTokens,expected.validTokens);
 }
});
