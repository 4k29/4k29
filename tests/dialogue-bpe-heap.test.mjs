import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createTokenizer} from '../training/dialogue/tokenizer.mjs';
import {createDialogueDecoder} from '../training/dialogue/inference.mjs';
import {dialogueModel} from '../training/dialogue/switch-candidate.js';
const read=name=>JSON.parse(fs.readFileSync(new URL('../training/dialogue/'+name,import.meta.url)));

test('adjacent BPE preserves merge rank and left-to-right overlap resolution',()=>{
 const specials={pad:0,bos:1,eos:2,user:3,assistant:4,turn:5};
 const bytes=[...Array(6).fill(''),...Array.from({length:256},(_,i)=>i.toString(16).padStart(2,'0')),'6161','616161','6162','61616161'];
 const config={specials,bytes,merges:[[103,103,262],[262,103,263],[103,104,264],[262,262,265]]};
 const plain=createTokenizer(config),fast=createTokenizer(config,{algorithm:'adjacent-heap'});
 for(const text of ['',...'a'.repeat(100).split('').map((_,i)=>'a'.repeat(i+1)),'ababaaaaaba','aaabaaaabaaa','😀日本語\n','\ud800','z'])assert.deepEqual(fast.encode(text),plain.encode(text),JSON.stringify(text));
 assert.throws(()=>createTokenizer(config,{algorithm:'external'}),RangeError);
});

test('heap and reference BPE agree on all unique current training, validation, test and control strings',()=>{
 const c=read('owner-aligned-corpus.json'),texts=new Set();
 for(const r of c.rows){texts.add(r.question);texts.add(r.answer);for(const h of r.history){texts.add(h.question);texts.add(h.answer);}}
 for(const r of read('owner-aligned-audit.json').rows){texts.add(r.question);texts.add(r.answer);}
 for(const conv of read('owner-aligned-rollouts.json').conversations)for(const r of conv.turns){texts.add(r.question);texts.add(r.answer);}
 for(const r of read('owner-aligned-raw-probes.json').rows){texts.add(r.prefix);texts.add(r.reference);}
 const plain=createTokenizer(c.tokenizer),fast=createTokenizer(c.tokenizer,{algorithm:'adjacent-heap'});
 for(const text of texts)assert.deepEqual(fast.encode(text),plain.encode(text),text);
 assert.ok(texts.size>13000);
});

test('fast tokenization leaves logits, greedy answers, beam answers and reset behavior unchanged',()=>{
 const plain=createDialogueDecoder(dialogueModel,{cachePrefixes:true}),fast=createDialogueDecoder(dialogueModel,{cachePrefixes:true,tokenizerAlgorithm:'adjacent-heap'});
 const history=[];
 for(const q of ['MERは？','Nothing Headphone (1)について詳しく教えて','LDACでANCオンの再生時間は？','好きなものは何']){
  assert.deepEqual(fast.tokenizer.prompt(q,history),plain.tokenizer.prompt(q,history));
  assert.deepEqual(fast.logits(fast.tokenizer.prompt(q,history)),plain.logits(plain.tokenizer.prompt(q,history)));
  const a=plain.generate(q,{history}),b=fast.generate(q,{history});assert.deepEqual(a,b);
  assert.deepEqual(fast.generateBeam(q,{history,beamSize:4}),plain.generateBeam(q,{history,beamSize:4}));
  if(a.eos&&a.validTokens)history.push({question:q,answer:a.text});
 }
 fast.clearCache();plain.clearCache();assert.deepEqual(fast.cacheStats(),plain.cacheStats());assert.deepEqual(fast.generate('趣味は何？'),plain.generate('趣味は何？'));
});
