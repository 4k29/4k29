import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {neuralModel as model} from '../docs/neural-model.js';
import {neuralModel as teacher} from '../training/transformer-teacher.js';
import {generationModel as grammar} from '../docs/generation-model.js';
import {directVoicePath} from '../docs/response-voice.js';
import {neuralLogits,neuralDistribution,neuralSequenceLikelihood,clearNeuralCache,neuralCacheInfo} from '../docs/neural-inference.js';
import {Conversation} from '../docs/dialogue.js';
const reference=JSON.parse(fs.readFileSync(new URL('../training/transformer-reference.json',import.meta.url)));
const trainingTrace=JSON.parse(fs.readFileSync(new URL('../training/transformer-training.json',import.meta.url)));
test('shipped Transformer has real learned tensors, held-out validation and matching vocabulary',()=>{
 assert.equal(model.config.layers,2);assert.equal(model.config.heads,4);assert.equal(model.training.parameters,33440);
 assert.equal(model.training.trainRows+model.training.validationRows,model.training.requestedRounds?grammar.paths.filter(p=>directVoicePath(p,grammar.vocabulary)).length+(model.training.completedRounds===10?24:0):grammar.paths.length);
 if(model.training.initialCheckpointStep){
  assert.ok(model.training.finalValidationLoss<=model.training.initialValidationLoss*1.02);
  assert.ok(Math.max(...model.tensors['token.weight'].data.map((v,i)=>Math.abs(v-teacher.tensors['token.weight'].data[i])))>1e-5);
 }else assert.ok(model.training.finalValidationLoss<model.training.initialValidationLoss*.4);
 assert.ok(model.training.bestStep<=model.training.completedSteps);
 assert.ok(model.training.completedSteps>=10000);assert.ok(model.training.bestStep>=10000);
 assert.deepEqual(model.vocabulary.slice(0,grammar.vocabulary.length),grammar.vocabulary);
 assert.equal(model.training.baseSourceSha256,grammar.training.sourceSha256);
 if(model.training.requestedRounds){
  assert.equal(model.training.requestedRounds,10);assert.equal(model.training.completedRounds,10);
  assert.equal(model.training.updatesPerRound,10000);assert.equal(model.training.completedSteps,100000);
  assert.equal(model.training.bestStep,100000);assert.equal(model.training.cumulativeCheckpointSteps,610700);
  assert.equal(model.training.checkpointPolicy,'after-all-requested-updates');
  const initialFile=fs.readFileSync(new URL('../training/transformer-500000-teacher.js',import.meta.url));
  assert.equal(model.training.initializedModelSha256,createHash('sha256').update(initialFile).digest('hex'));
  assert.equal(trainingTrace.rounds.length,10);
  for(const [index,round] of trainingTrace.rounds.entries()){assert.equal(round.round,index+1);assert.equal(round.updates,(index+1)*10000);assert.ok(Number.isFinite(round.validationLoss));}
 }
 for(const tensor of Object.values(model.tensors)){assert.equal(tensor.shape.reduce((n,d)=>n*d,1),tensor.data.length);assert.ok(tensor.data.every(Number.isFinite));}
});
for(const [index,row] of reference.references.entries())test('browser inference agrees with PyTorch, case '+index,()=>{
 assert.equal(reference.version,model.version);const logits=neuralLogits(row.context,row.tokens.slice(4));
 assert.equal(logits.length,row.logits.length);const worst=Math.max(...logits.map((value,i)=>Math.abs(value-row.logits[i])));assert.ok(worst<1e-4,String(worst));
});
test('autoregressive softmax normalizes and responds to context and requested style',()=>{
 const context={language:'ja',kind:'name',style:'friendly'},value=grammar.vocabulary.indexOf('{value}');
 const start=neuralDistribution(context,[]),after=neuralDistribution(context,[value]),polite=neuralDistribution({...context,style:'polite'},[value]);
 for(const probabilities of [start,after,polite]){assert.ok(Math.abs(probabilities.reduce((a,b)=>a+b,0)-1)<1e-6);assert.ok(probabilities.every(p=>p>=0&&Number.isFinite(p)));}
 assert.ok(Math.max(...after.map((p,i)=>Math.abs(p-start[i])))>.03);
 assert.ok(Math.max(...after.map((p,i)=>Math.abs(p-polite[i])))>.03);
});
test('causal state is immutable across future tokens and its cache stays bounded',()=>{
 clearNeuralCache();const context={language:'ja',kind:'name',style:'friendly'},tokens=grammar.paths.find(p=>p.language==='ja'&&p.kind==='name'&&p.style==='friendly').tokens;
 const before=Array.from(neuralLogits(context,tokens.slice(0,2)));neuralLogits(context,tokens);assert.deepEqual(Array.from(neuralLogits(context,tokens.slice(0,2))),before);
 for(let i=0;i<700;i++)neuralLogits(context,[i%grammar.vocabulary.length,Math.floor(i/grammar.vocabulary.length)+3]);
 assert.ok(neuralCacheInfo().size<=neuralCacheInfo().limit);clearNeuralCache();assert.equal(neuralCacheInfo().size,0);
});
test('complete trained paths get finite likelihood and factual replies use the neural engine',()=>{
 for(const p of grammar.paths.slice(0,10)){const score=neuralSequenceLikelihood(p,p.tokens);assert.ok(Number.isFinite(score.meanLogProbability)&&score.meanLogProbability<0);}
 const data=JSON.parse(fs.readFileSync(new URL('../docs/profile.json',import.meta.url))),a=new Conversation(data).respond('名前は？');
 assert.equal(a.generation.model,model.version);assert.equal(a.generation.algorithm,'causal-transformer');assert.deepEqual(a.factIds,['name']);
});
