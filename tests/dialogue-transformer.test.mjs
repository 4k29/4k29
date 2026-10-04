import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {dialogueModel} from '../training/dialogue/candidate.js';
import {dialogueModel as semanticModel} from '../training/dialogue/semantic-candidate.js';
import {createDialogueDecoder} from '../training/dialogue/inference.mjs';
import {createTokenizer} from '../training/dialogue/tokenizer.mjs';
const corpus=JSON.parse(fs.readFileSync(new URL('../training/dialogue/corpus.json',import.meta.url)));
const reference=JSON.parse(fs.readFileSync(new URL('../training/dialogue/experiment-reference.json',import.meta.url)));
const decoder=createDialogueDecoder(dialogueModel);
test('own end-to-end model trains full answers from random weights without a teacher',()=>{
 assert.equal(dialogueModel.training.randomInitialization,true);assert.equal(dialogueModel.training.externalWeights,false);assert.equal(dialogueModel.training.teacher,false);
 assert.equal(dialogueModel.training.completedSteps,10000);assert.equal(dialogueModel.config.layers,2);assert.equal(dialogueModel.training.parameters,116608);
 assert.equal(dialogueModel.training.sourceSha256,corpus.sourceSha256);
 const groups=p=>new Set(corpus.rows.filter(r=>r.partition===p).map(r=>r.group));const train=groups('train');
 for(const p of ['validation','test'])assert.ok([...groups(p)].every(group=>!train.has(group)));
 const source={...corpus};delete source.sourceSha256;assert.equal(createHash('sha256').update(JSON.stringify(source)).digest('hex'),corpus.sourceSha256);
 for(const t of Object.values(dialogueModel.tensors)){assert.equal(t.shape.reduce((n,d)=>n*d,1),t.data.length);assert.ok(t.data.every(Number.isFinite));}
 for(const row of corpus.rows){assert.ok(row.prefixLength<row.tokens.length);assert.equal(row.tokens.at(-1),corpus.tokenizer.specials.eos);assert.ok(row.tokens.length<=dialogueModel.config.context);}
});
test('own byte BPE has deterministic UTF-8 fallback and round trips unseen text',()=>{
 const t=createTokenizer(corpus.tokenizer);
 for(const text of ['こんにちは。','Nothing Headphone (1)は329gです。','未学習の漢字𠮷と絵文字🦉','ABC abc 123','\n\t'])assert.equal(t.decode(t.encode(text)),text);
 for(const row of corpus.rows){assert.deepEqual(t.prompt(row.question,row.history),row.tokens.slice(0,row.prefixLength));assert.equal(t.decode(row.tokens.slice(row.prefixLength,-1)),row.answer);}
 assert.ok(corpus.tokenizer.bytes.every(hex=>hex.length/2<=12));
});
for(const [index,row] of reference.references.entries())test('incremental JavaScript matches PyTorch for complete question, case '+index,()=>{
 assert.equal(reference.version,dialogueModel.version);const logits=decoder.logits(row.tokens);
 assert.ok(Math.max(...logits.map((v,i)=>Math.abs(v-row.logits[i])))<0.0002);
});
test('question/history conditions the output and excessive input is rejected',()=>{
 const mer=decoder.tokenizer.prompt('MERは？'),vivant=decoder.tokenizer.prompt('VIVANTは？');
 const left=decoder.logits(mer),right=decoder.logits(vivant);assert.ok(Math.max(...left.map((v,i)=>Math.abs(v-right[i])))>0.1);
 assert.throws(()=>decoder.generate('長い質問'.repeat(200)),/context/i);
});
test('full model generation uses learned tokens rather than protected answer slots',()=>{
 for(const question of ['名前は何？','MERは？','趣味は何？']){
  const a=decoder.generate(question);assert.ok(a.eos);assert.ok(a.validTokens);assert.ok(a.tokens.length>1);assert.doesNotMatch(a.text,/\{value\}|NaN|undefined|�/);
 }
});
test('training-only intent head leaves the same independently executable decoder interface',()=>{
 assert.equal(semanticModel.training.parameters,118038);assert.equal(semanticModel.training.completedSteps,10000);
 assert.equal(semanticModel.training.intentLossWeight,0.3);assert.equal(semanticModel.training.intentHeadUsedAtInference,false);
 const semantic=createDialogueDecoder(semanticModel),refs=JSON.parse(fs.readFileSync(new URL('../training/dialogue/semantic-reference.json',import.meta.url)));
 for(const row of refs.references){const actual=semantic.logits(row.tokens);assert.ok(Math.max(...actual.map((v,i)=>Math.abs(v-row.logits[i])))<0.0002);}
});
