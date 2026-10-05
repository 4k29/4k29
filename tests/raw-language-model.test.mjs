import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {dialogueModel as model} from '../training/language/raw-million/model.js';
import {createDialogueDecoder} from '../training/dialogue/inference.mjs';
const root=new URL('../training/language/',import.meta.url),read=p=>JSON.parse(fs.readFileSync(new URL(p,root))),sha=p=>createHash('sha256').update(fs.readFileSync(new URL(p,root))).digest('hex');

test('million-parameter own raw decoder completes actual10000 optimizer updates without instruction or outside models',()=>{
 const t=model.training,data=read('bpe-4096/data.json'),config=read('raw-million/config.json');assert.equal(t.completedRun,true);assert.equal(t.completedSteps,10000);assert.equal(t.requestedSteps,10000);assert.equal(t.randomInitialization,true);assert.equal(t.externalWeights,false);assert.equal(t.externalTokenizer,false);assert.equal(t.externalInferenceAPI,false);assert.match(t.objective,/Raw original document causal next-token/);assert.match(t.objective,/no QA, instruction tuning or teacher/);
 assert.equal(t.sourceSha256,data.sourceSha256);assert.equal(t.splitSha256,data.splitSha256);assert.equal(t.tokenizerSha256,sha('bpe-4096/tokenizer.json'));assert.deepEqual(model.tokenizer,read('bpe-4096/tokenizer.json'));
 assert.equal(t.checkpointSha256,sha('raw-million/checkpoint.pt'));assert.equal(t.parameters,2665728);assert.deepEqual(model.config,config.config);assert.equal(model.config.context,256);assert.equal(model.config.dim,192);assert.equal(model.config.layers,4);assert.equal(model.config.hidden,768);
 assert.ok(Object.keys(model.tensors).every(k=>!k.startsWith('semantic.')));
 let count=0;for(const tensor of Object.values(model.tensors)){assert.equal(tensor.data.length,tensor.shape.reduce((a,b)=>a*b,1));assert.ok(tensor.data.every(Number.isFinite));count+=tensor.data.length;}assert.equal(count,t.parameters);
 const metrics=read('raw-million/metrics.json');assert.equal(metrics.history.length,21);assert.equal(metrics.history.at(-1).step,10000);const best=metrics.history.toSorted((a,b)=>a.validation.nllPerUtf8Byte-b.validation.nllPerUtf8Byte)[0];assert.equal(t.bestStep,best.step);
 assert.ok(best.validation.nllPerUtf8Byte<metrics.history[0].validation.nllPerUtf8Byte);assert.equal(read('vocabulary-choice.json').selectedMerges,4096);
});

test('raw TEST inference agrees independently on full tokens, original openings, invalidity and EOS without answer repair',()=>{
 const py=read('raw-million/test.json'),js=read('raw-million/test-js.json');assert.equal(py.rows.length,22);assert.equal(js.rows.length,22);assert.equal(py.modelFileSha256,sha('raw-million/model.js'));assert.equal(js.modelSha256,sha('raw-million/model.js'));assert.equal(js.completeGenerationParity,true);
 const references=new Map(py.rows.map(r=>[r.id,r]));for(const r of js.rows)for(const key of ['text','tokens','eos','validUtf8','validTokens','inputTokens'])assert.deepEqual(r[key],references.get(r.id)[key],r.id+':'+key);
 const decoder=createDialogueDecoder(model);for(const r of py.references){const logits=decoder.logits(r.tokens);assert.ok(Math.max(...logits.map((v,i)=>Math.abs(v-r.logits[i])))<.0002,r.id);}
 for(const r of js.references)assert.ok(r.maxAbsoluteError<.0002,r.id);
});

test('raw inference preserves Japanese/Latin case and outputs without training metadata, alternative BPE or cache assistance',()=>{
 const bare={...model,training:null},decoder=createDialogueDecoder(model),cached=createDialogueDecoder(bare,{cachePrefixes:true,tokenizerAlgorithm:'adjacent-heap'}),fast=createDialogueDecoder(bare,{tokenizerAlgorithm:'adjacent-heap'});
 const opening='Appleの製品は、日本語の文章';const expected=decoder.generateRaw(opening,{maxNewTokens:32});assert.deepEqual(fast.generateRaw(opening,{maxNewTokens:32}),expected);assert.deepEqual(cached.generateRaw(opening,{maxNewTokens:32}),expected);assert.deepEqual(cached.generateRaw(opening,{maxNewTokens:32}),expected);
 assert.equal(expected.inputTokens,1+decoder.tokenizer.encode(opening).length);assert.ok(cached.cacheStats().reusedPrefixTokens>0);
 cached.clearCache();assert.deepEqual(cached.generateRaw(opening,{maxNewTokens:32}),expected);
 assert.throws(()=>decoder.generateRaw('日'.repeat(2000)),RangeError);
});

test('language acceptance is independently recomputable from all explicit judgments and keeps failures visible',()=>{
 const raw=read('raw-million/test.json'),review=read('raw-million/test-review.json'),manual=read('raw-million/test-manual-review.json'),policy=read('generation-policy.json');assert.equal(review.generationSha256,sha('raw-million/test.json'));assert.equal(manual.generationSha256,review.generationSha256);assert.equal(review.total,22);assert.equal(review.independentHumanEvaluation,false);
 const rows=new Map(manual.rows.map(r=>[r.id,r]));let passed=0;
 for(const output of raw.rows){const r=rows.get(output.id);assert.ok(r.reason);const total=['grammar','meaning','connection','repetition','breaks'].reduce((n,k)=>n+r[k],0);const valid=total>=9&&r.grammar===2&&r.connection===2&&r.sentenceClosed&&output.validTokens;assert.equal(review.rows.find(x=>x.id===output.id).firstSentencePass,valid);if(valid)passed++;}
 assert.equal(review.passed,passed);for(const [name,group] of Object.entries(review.groups)){const subset=review.rows.filter(r=>(r.site==='aozora')===(name==='narrative'));assert.equal(group.total,subset.length);assert.equal(group.gatePassed,group.firstSentenceSuccessRate>=policy.acceptance.minimumSentenceSuccessRate&&group.fullOutputNonLoopRate>=policy.acceptance.minimumFullOutputNonLoopRate);}
 assert.equal(review.gatePassed,Object.values(review.groups).every(g=>g.gatePassed));
});
