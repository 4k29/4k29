import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {dialogueModel as model} from '../training/dialogue/owner-aligned-candidate.js';
import {dialogueModel as parent} from '../training/dialogue/switch-candidate.js';
import {createDialogueDecoder} from '../training/dialogue/inference.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL('../training/dialogue/'+name,import.meta.url)));
const corpus=read('owner-aligned-corpus.json');

test('own revised training records true lineage, confirmed suspended7500 updates and validation-only selection',()=>{
 const t=model.training;assert.equal(t.completedRun,false);assert.equal(t.completedSteps,7500);assert.equal(t.pretrainingUpdates,1000);assert.equal(t.dialogueUpdates,6500);assert.equal(t.requestedDialogueUpdates,10000);
 assert.equal(t.randomInitialization,false);assert.equal(t.initializationKind,'own-dialogue-model-continuation');assert.equal(t.externalWeights,false);assert.equal(t.externalInferenceAPIs,false);assert.equal(t.teacher,false);
 assert.equal(t.sourceSha256,corpus.sourceSha256);assert.equal(t.ownInitialModel.sourceSha256,parent.training.sourceSha256);assert.equal(t.ownInitialModel.selectedParentStep,9000);assert.equal(t.ownInitialModel.completedParentUpdates,11000);assert.equal(t.ownInitialModel.optimizerReused,false);
 assert.deepEqual(model.tokenizer,parent.tokenizer);assert.equal(model.config.context,512);assert.equal(t.ownInitialModel.extendedPositionEmbeddings.parent,256);assert.equal(t.ownInitialModel.extendedPositionEmbeddings.current,512);
 const selection=read('owner-aligned-validation-selection.json');assert.equal(t.validationSelectionSha256,selection.idsSha256);assert.equal(t.validationRows,256);
 const history=read('owner-aligned-training.json').history.filter(r=>r.stage==='dialogue');assert.equal(history.length,6);
 const best=history.toSorted((a,b)=>b.validationExact-a.validationExact||a.validationLoss-b.validationLoss)[0];assert.equal(t.bestStep,best.step);assert.equal(t.validationExact,best.validationExact);assert.equal(t.validationLoss,best.validationLoss);
});

test('trained tensors are finite and independent full-prefix PyTorch logits agree across extended positions',()=>{
 for(const tensor of Object.values(model.tensors)){assert.equal(tensor.data.length,tensor.shape.reduce((a,b)=>a*b,1));assert.ok(tensor.data.every(Number.isFinite));}
 const decoder=createDialogueDecoder(model),refs=[...read('owner-aligned-reference.json').references,...read('owner-aligned-extended-reference.json').references];
 assert.ok(refs.some(r=>r.tokens.length>256));
 for(const r of refs){const actual=decoder.logits(r.tokens);assert.equal(actual.length,r.logits.length);assert.ok(Math.max(...actual.map((v,i)=>Math.abs(v-r.logits[i])))<0.0002,r.id);}
 const generating=Object.entries(model.tensors).filter(([key])=>!key.startsWith('semantic.')).reduce((n,[,t])=>n+t.data.length,0);assert.equal(generating,627840);assert.equal(model.training.parameters,644094);
});

test('suspended optimizer checkpoint is preserved with its actual completed-update count',()=>{
 const suspended=read('owner-aligned-suspended/SUSPENDED.json');
 const checkpoint=fs.readFileSync(new URL('../training/dialogue/owner-aligned-suspended/checkpoint.pt',import.meta.url));
 assert.equal(createHash('sha256').update(checkpoint).digest('hex'),suspended.checkpointSha256);
 assert.equal(suspended.confirmedCompletedUpdatesAtCheckpoint,model.training.completedSteps);
 assert.equal(suspended.selectedStep,model.training.bestStep);
 assert.equal(suspended.publishedModelReplaced,false);
});

test('inference answers depend on generating weights without training-only labels or metadata',()=>{
 const stripped={...model,training:null,config:{...model.config,semanticTasks:undefined},tensors:Object.fromEntries(Object.entries(model.tensors).filter(([key])=>!key.startsWith('semantic.')))};
 const full=createDialogueDecoder(model),bare=createDialogueDecoder(stripped),fast=createDialogueDecoder(stripped,{tokenizerAlgorithm:'adjacent-heap'});
 for(const q of ['Apple','好きなものは何','Nothing Headphone (1)について詳しく教えて','興味のあるものは何']){const answer=full.generate(q);assert.deepEqual(bare.generate(q),answer);assert.deepEqual(fast.generate(q),answer);}
});
