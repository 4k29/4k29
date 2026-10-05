import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {dialogueModel as model} from '../training/language/paragraph-million/model.js';
import {createDialogueDecoder} from '../training/dialogue/inference.mjs';
const root=new URL('../training/language/',import.meta.url),read=p=>JSON.parse(fs.readFileSync(new URL(p,root))),sha=p=>createHash('sha256').update(fs.readFileSync(new URL(p,root))).digest('hex');

test('raw paragraph continuation preserves own source/tokenizer lineage and actual update accounting',()=>{
 const t=model.training,data=read('paragraph-bpe-4096/data.json'),parent=read('raw-million/result.json');
 assert.equal(t.completedRun,true);assert.equal(t.completedSteps,10000);assert.equal(t.randomInitialization,false);assert.equal(t.parentRandomInitialization,true);
 assert.equal(t.ownInitialModel.checkpointSha256,sha('raw-million/checkpoint.pt'));assert.equal(t.ownInitialModel.completedParentUpdates,parent.completedSteps);assert.equal(t.ownInitialModel.selectedParentStep,parent.bestStep);assert.equal(t.ownInitialModel.optimizerReused,false);
 for(const k of ['externalWeights','externalTokenizer','externalInferenceAPI'])assert.equal(t[k],false);
 assert.match(t.objective,/no QA, instruction tuning or teacher/);assert.equal(t.paragraphSelectionsSha256,data.paragraphSelectionsSha256);assert.equal(t.sourceSha256,data.sourceSha256);assert.equal(t.splitSha256,data.splitSha256);assert.equal(t.tokenizerSha256,sha('bpe-4096/tokenizer.json'));assert.deepEqual(model.tokenizer,read('bpe-4096/tokenizer.json'));assert.equal(t.checkpointSha256,sha('paragraph-million/checkpoint.pt'));assert.equal(t.parameters,2665728);
 const metrics=read('paragraph-million/metrics.json');assert.equal(metrics.history.at(-1).step,10000);assert.equal(t.bestStep,metrics.history.toSorted((a,b)=>a.validation.nllPerUtf8Byte-b.validation.nllPerUtf8Byte)[0].step);
 assert.ok(Object.keys(model.tensors).every(k=>!k.startsWith('semantic.')));let count=0;for(const tensor of Object.values(model.tensors)){assert.ok(tensor.data.every(Number.isFinite));assert.equal(tensor.data.length,tensor.shape.reduce((a,b)=>a*b,1));count+=tensor.data.length;}assert.equal(count,t.parameters);
});

test('paragraph model TEST generation and likelihood preserve the evaluation unit and independent inference parity',()=>{
 const py=read('paragraph-million/test.json'),js=read('paragraph-million/test-js.json');assert.equal(py.modelFileSha256,sha('paragraph-million/model.js'));assert.equal(py.likelihoodDataDirectory,'paragraph-bpe-4096');assert.equal(py.rows.length,22);assert.equal(js.completeGenerationParity,true);assert.equal(js.modelSha256,sha('paragraph-million/model.js'));
 const rows=new Map(py.rows.map(r=>[r.id,r]));assert.equal(js.rows.length,rows.size);for(const r of js.rows)for(const k of ['tokens','text','eos','validTokens','validUtf8','inputTokens'])assert.deepEqual(r[k],rows.get(r.id)[k],r.id+':'+k);
 const decoder=createDialogueDecoder(model);for(const r of py.references){const logits=decoder.logits(r.tokens);assert.ok(Math.max(...logits.map((v,i)=>Math.abs(v-r.logits[i])))<.0002,r.id);}
});

test('paragraph model language scores retain every failure and apply the unchanged pretraining gate',()=>{
 const py=read('paragraph-million/test.json'),manual=read('paragraph-million/test-manual-review.json'),review=read('paragraph-million/test-review.json'),policy=read('generation-policy.json');assert.equal(manual.generationSha256,sha('paragraph-million/test.json'));assert.equal(review.generationSha256,manual.generationSha256);assert.equal(review.total,22);assert.equal(review.independentHumanEvaluation,false);assert.deepEqual(review.frozenAcceptance,policy.acceptance);
 const ratings=new Map(manual.rows.map(r=>[r.id,r]));for(const row of review.rows){const j=ratings.get(row.id);assert.ok(j.reason);assert.equal(row.firstSentencePass,['grammar','meaning','connection','repetition','breaks'].reduce((n,k)=>n+j[k],0)>=9&&j.grammar===2&&j.connection===2&&j.sentenceClosed&&py.rows.find(r=>r.id===row.id).validTokens);}
 assert.equal(review.passed,review.rows.filter(r=>r.firstSentencePass).length);for(const [name,g] of Object.entries(review.groups)){const rows=review.rows.filter(r=>(r.site==='aozora')===(name==='narrative'));assert.equal(g.firstSentencePassed,rows.filter(r=>r.firstSentencePass).length);assert.equal(g.fullOutputNonLoop,rows.filter(r=>!r.manual.fullOutputLoop).length);assert.equal(g.gatePassed,g.firstSentenceSuccessRate>=.8&&g.fullOutputNonLoopRate>=.9);}assert.equal(review.gatePassed,Object.values(review.groups).every(g=>g.gatePassed));
});
