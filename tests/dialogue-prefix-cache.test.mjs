import test from 'node:test';
import assert from 'node:assert/strict';
import {dialogueModel} from '../training/dialogue/continuous-candidate.js';
import {createDialogueDecoder} from '../training/dialogue/inference.mjs';
const pair=()=>[createDialogueDecoder(dialogueModel),createDialogueDecoder(dialogueModel,{cachePrefixes:true})];

test('KV prefix reuse preserves complete answers through actual generated history',()=>{
 const [plain,cached]=pair(),history=[];
 for(const question of ['MERは？','VIVANTは？','最後のドラマの主演は？','ありがとう。']){
  const expected=plain.generate(question,{history}),actual=cached.generate(question,{history});assert.deepEqual(actual,expected);
  const stats=cached.cacheStats();assert.ok(stats.storedTokens<=dialogueModel.config.context);assert.equal(stats.storedStates,stats.storedTokens+1);
  if(history.length)assert.ok(stats.reusedPrefixTokens>2);
  if(actual.eos&&actual.validTokens)history.push({question,answer:actual.text});
 }
});

test('changing early history safely discards divergent cached states',()=>{
 const [plain,cached]=pair();
 const left=[{question:'MERは？',answer:'TOKYO MERです。'}],right=[{question:'VIVANTは？',answer:'VIVANTです。'}];
 for(const history of [left,right,left,[]])assert.deepEqual(cached.generate('主演は？',{history}),plain.generate('主演は？',{history}));
});

test('a partial answer tokenization is never treated as a cached complete response',()=>{
 const [plain,cached]=pair();const first=cached.generate('Stringとは？',{maxNewTokens:1});
 const history=[{question:'Stringとは？',answer:first.text}];
 assert.deepEqual(cached.generate('MERは？',{history}),plain.generate('MERは？',{history}));
 // A repeated input recomputes output logits instead of returning a text cache.
 assert.deepEqual(cached.generate('MERは？'),plain.generate('MERは？'));
});

test('cache reset releases the conversation path and preserves independent logits',()=>{
 const [plain,cached]=pair();cached.generate('Headphone1の重さは？');cached.clearCache();
 assert.deepEqual(cached.cacheStats(),{enabled:true,reusedPrefixTokens:0,storedTokens:0,storedStates:1});
 const prefix=plain.tokenizer.prompt('趣味は何？');assert.deepEqual(cached.logits(prefix),plain.logits(prefix));
});

test('invalid logits inputs fail repeatedly without poisoning the cached path',()=>{
 const [plain,cached]=pair();
 for(const tokens of [[1,-1],Array(dialogueModel.config.context+1).fill(3)])for(let i=0;i<2;i++){
  assert.throws(()=>cached.logits(tokens),RangeError);assert.throws(()=>plain.logits(tokens),RangeError);
 }
 assert.deepEqual(cached.generate('MERは？'),plain.generate('MERは？'));
});
