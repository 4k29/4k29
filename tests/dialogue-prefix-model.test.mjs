import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {dialogueModel} from '../training/dialogue/prefix-corrected-candidate.js';
import {createDialogueDecoder} from '../training/dialogue/inference.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL('../training/dialogue/'+name,import.meta.url)));
const decoder=createDialogueDecoder(dialogueModel);

test('prefix experiment executes own random 1000+10000 training without outside weights',()=>{
 const t=dialogueModel.training;
 assert.equal(t.completedSteps,11000);assert.equal(t.pretrainingUpdates,1000);assert.equal(t.dialogueUpdates,10000);
 assert.equal(t.randomInitialization,true);assert.equal(t.initializationKind,'random');assert.equal(t.ownPretrainingParent,null);
 assert.equal(t.externalWeights,false);assert.equal(t.externalInferenceAPIs,false);assert.equal(t.teacher,false);
 assert.equal(t.parameters,426642);assert.equal(dialogueModel.config.dim,96);assert.equal(dialogueModel.config.context,192);
 assert.equal(t.settings.answer_prefix_weight,2);assert.equal(t.settings.answer_prefix_tokens,8);
 assert.equal(t.sourceSha256,read('prefix-corrected-corpus.json').sourceSha256);
 assert.equal(Object.values(dialogueModel.tensors).reduce((n,t)=>n+t.data.length,0),426642);
});

test('prefix semantic heads do not supply any answer or alter inference',()=>{
 const config={...dialogueModel.config};delete config.semanticTasks;
 const tensors=Object.fromEntries(Object.entries(dialogueModel.tensors).filter(([name])=>!name.startsWith('semantic.')));
 const plain=createDialogueDecoder({...dialogueModel,config,tensors});
 for(const q of ['MERは？','Headphone1の重量は？','Stringとは？']){
  assert.deepEqual(decoder.logits(decoder.tokenizer.prompt(q)),plain.logits(plain.tokenizer.prompt(q)));
  assert.deepEqual(decoder.generate(q),plain.generate(q));
 }
});

for(const [i,row] of read('prefix-corrected-reference.json').references.entries())test('prefix independent logits match PyTorch '+i,()=>{
 const actual=decoder.logits(row.tokens);assert.ok(Math.max(...actual.map((v,j)=>Math.abs(v-row.logits[j])))<0.0002);
});

for(const [pythonFile,jsFile,total] of [['prefix-corrected-test-results.json','prefix-corrected-js-results.json',928],['prefix-corrected-audit-results.json','prefix-corrected-audit-js-results.json',100]])test('prefix full generation agrees across independent runtimes '+pythonFile,()=>{
 const python=read(pythonFile),js=read(jsFile);
 assert.equal(python.total,total);assert.equal(js.total,total);assert.equal(python.exact,js.exact);
 const byId=new Map(python.rows.map(r=>[r.id,r]));
 for(const row of js.rows){const expected=byId.get(row.id);assert.equal(row.answer,expected.answer);assert.equal(row.eos,expected.eos);assert.equal(row.validTokens,expected.validTokens);}
});
