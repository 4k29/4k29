import test from 'node:test';
import assert from 'node:assert/strict';
import {beamSearch} from '../training/dialogue/beam_search.mjs';
import {dialogueModel} from '../training/dialogue/continuous-candidate.js';
import {createDialogueDecoder} from '../training/dialogue/inference.mjs';
const probabilities=path=>path.length===0?[.01,.6,.39]:path.length===1&&path[0]===1?[.25,.01,.74]:path.length===1?[.95,.04,.01]:[.8,.1,.1];
const search=(size,penalty=0)=>beamSearch({state:[],logits:path=>probabilities(path).map(Math.log),advance:(path,t)=>[...path,t],eos:0,beamSize:size,lengthPenalty:penalty,maxSteps:3});

test('own beam search escapes a locally best token and matches exhaustive finished paths',()=>{
 assert.deepEqual(search(1).tokens,[1,2]);assert.deepEqual(search(8).tokens,[2]);
 for(const penalty of [0,.6,1]){
  const results=[];
  function enumerate(path,p){const probs=probabilities(path);results.push({tokens:path,score:Math.log(p*probs[0])/((5+path.length+1)/6)**penalty});if(path.length<2)for(const id of [1,2])enumerate([...path,id],p*probs[id]);}
  enumerate([],1);results.sort((a,b)=>b.score-a.score);const result=search(8,penalty);
  assert.deepEqual(result.tokens,results[0].tokens);assert.ok(Math.abs(result.score-results[0].score)<1e-12);
 }
});

test('impossible EOS respects budget and invalid search settings fail',()=>{
 const options={state:[],logits:()=>[-Infinity,0],advance:(p,t)=>[...p,t],eos:0,beamSize:2,lengthPenalty:.6,maxSteps:3};
 const r=beamSearch(options);assert.equal(r.eos,false);assert.deepEqual(r.tokens,[1,1,1]);
 for(const beamSize of [0,17,1.5])assert.throws(()=>beamSearch({...options,beamSize}),RangeError);
});

test('one beam keeps historical greedy behavior and independent branches preserve cache parity',()=>{
 const plain=createDialogueDecoder(dialogueModel),cached=createDialogueDecoder(dialogueModel,{cachePrefixes:true});
 for(const q of ['MERは？','趣味は何？']){
  assert.deepEqual(plain.generateBeam(q,{beamSize:1}),plain.generate(q));
  assert.deepEqual(cached.generateBeam(q,{beamSize:3,maxNewTokens:24}),plain.generateBeam(q,{beamSize:3,maxNewTokens:24}));
 }
 assert.deepEqual(cached.generate('VIVANTは？'),plain.generate('VIVANTは？'));
});
