import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {dialogueModel} from '../training/dialogue/generalization-candidate.js';
import {dialogueModel as webModel} from '../training/dialogue/web-curriculum-candidate.js';
import {dialogueModel as replayModel} from '../training/dialogue/web-replay-candidate.js';
import {createDialogueDecoder} from '../training/dialogue/inference.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL('../training/dialogue/'+name,import.meta.url)));
const corpus=read('generalization-corpus.json'),decoder=createDialogueDecoder(dialogueModel);
test('curriculum really performs own raw pretraining and full-answer SFT',()=>{
 assert.equal(dialogueModel.training.randomInitialization,true);assert.equal(dialogueModel.training.externalWeights,false);assert.equal(dialogueModel.training.externalInferenceAPIs,false);
 assert.equal(dialogueModel.training.pretrainingUpdates,1000);assert.equal(dialogueModel.training.dialogueUpdates,10000);assert.equal(dialogueModel.training.completedSteps,11000);
 assert.equal(dialogueModel.training.parameters,335712);assert.equal(dialogueModel.training.sourceSha256,corpus.sourceSha256);
 for(const t of Object.values(dialogueModel.tensors)){assert.equal(t.shape.reduce((n,d)=>n*d,1),t.data.length);assert.ok(t.data.every(Number.isFinite));}
});
test('raw replay continues only our selected own pretraining and counts new updates separately',()=>{
 const training=replayModel.training;
 assert.equal(training.initializationKind,'own-raw-pretraining-continuation');
 assert.equal(training.externalWeights,false);assert.equal(training.externalInferenceAPIs,false);
 assert.equal(training.completedSteps,10000);assert.equal(training.pretrainingUpdates,0);
 assert.equal(training.dialogueUpdates,10000);assert.equal(training.inheritedOwnPretrainingUpdates,750);
 assert.equal(training.ownPretrainingParent.sourceSha256,webModel.training.sourceSha256);
 assert.equal(training.ownPretrainingParent.confirmedParentUpdates,13000);
 assert.equal(training.ownPretrainingParent.selectedRawStep,webModel.training.selectedPretrainingStep);
 assert.equal(training.settings.replay_weight,0.15);
});
test('web language documents and raw token chunks cannot leak across train/validation/test',()=>{
 const source=read('web-curriculum-corpus.json'),tokenizer=createDialogueDecoder(replayModel).tokenizer;
 const docs=new Map();
 for(const [key,partition] of [['pretraining','train'],['pretrainingValidation','validation'],['pretrainingTest','test']]){
  for(const row of source[key]){
   assert.ok(!docs.has(row.document)||docs.get(row.document)===partition);docs.set(row.document,partition);
   assert.equal(tokenizer.decode(row.tokens.slice(1,-1),{fatal:true}),row.text);
   assert.deepEqual(tokenizer.encode(row.text),row.tokens.slice(1,-1));
  }
 }
 // Hash the original Python JSON bytes: reserializing in JavaScript changes
 // integer-valued floats such as sampling weight 1.0 into 1.
 const payload=fs.readFileSync(new URL('../training/dialogue/web-curriculum-corpus.json',import.meta.url),'utf8').trim().replace(/,"sourceSha256":"[0-9a-f]{64}"\}$/, '}');
 assert.equal(createHash('sha256').update(payload).digest('hex'),source.sourceSha256);
 assert.equal(source.sourceSha256,replayModel.training.sourceSha256);
 // Even document-disjoint pages can produce identical short chunk endings.
 // The held-out language evaluator removes every train/validation overlap.
 const seen=new Set([...source.pretraining,...source.pretrainingValidation].map(r=>r.text));
 const held=source.pretrainingTest.filter(r=>!seen.has(r.text));
 const evaluation=read('web-replay-language-results.json');
 assert.equal(evaluation.samples,held.length);
 assert.deepEqual(evaluation.excludedSharedChunks,source.pretrainingTest.filter(r=>seen.has(r.text)).map(r=>({document:r.document,text:r.text})));
});
for(const [name,model] of [['web-curriculum',webModel],['web-replay',replayModel]]){
 const runtime=createDialogueDecoder(model);
 for(const [i,ref] of read(name+'-reference.json').references.entries())test(name+' matches independently exported PyTorch logits '+i,()=>{
  const actual=runtime.logits(ref.tokens);
  assert.ok(Math.max(...actual.map((v,j)=>Math.abs(v-ref.logits[j])))<0.0002);
 });
}
test('JavaScript and PyTorch freely generate the same full replay regression answers',()=>{
 const python=read('web-replay-regression-results.json'),js=read('web-replay-js-results.json');
 assert.equal(js.version,python.version);assert.equal(js.sourceSha256,python.sourceSha256);
 assert.equal(js.total,python.total);assert.equal(js.exact,python.exact);
 const byId=new Map(python.rows.map(row=>[row.id,row]));
 for(const row of js.rows){const expected=byId.get(row.id);assert.ok(expected);assert.equal(row.answer,expected.answer);assert.equal(row.eos,expected.eos);assert.equal(row.validTokens,expected.validTokens);}
});
test('full questions/history and question families never cross curriculum partitions',()=>{
 const groups={},inputs={};
 for(const row of corpus.rows){
  const key=JSON.stringify([row.question,row.history]);
  assert.ok(!groups[row.group]||groups[row.group]===row.partition);groups[row.group]=row.partition;
  assert.ok(!inputs[key]||inputs[key]===row.partition);inputs[key]=row.partition;
  assert.deepEqual(decoder.tokenizer.prompt(row.question,row.history),row.tokens.slice(0,row.prefixLength));
  assert.equal(decoder.tokenizer.decode(row.tokens.slice(row.prefixLength,-1)),row.answer);
 }
 const source={...corpus};delete source.sourceSha256;
 assert.equal(createHash('sha256').update(JSON.stringify(source)).digest('hex'),corpus.sourceSha256);
 const testRows=corpus.rows.filter(r=>r.partition==='test');
 assert.equal(createHash('sha256').update(JSON.stringify(testRows)).digest('hex'),dialogueModel.training.testSha256);
});
test('unsupported models and unverified personal information have explicit unknown training examples',()=>{
 const unknown=corpus.rows.filter(r=>r.partition==='train'&&r.kind==='unknown');
 assert.ok(unknown.some(r=>r.question.includes('headphone2')));
 assert.ok(unknown.some(r=>r.question.includes('誕生日')));
 assert.ok(unknown.some(r=>r.question.includes('友達のヘッドホン')));
 assert.ok(unknown.every(r=>r.answer==='その情報は分かりません。'));
});
test('incomplete UTF-8 cannot count as a valid generated Japanese answer',()=>{
 // Byte fallback token for 0xe3 is only the start of a Japanese UTF-8 character.
 assert.throws(()=>decoder.tokenizer.decode([6+0xe3],{fatal:true}));
 const text='𠮷という漢字と🦉';assert.equal(decoder.tokenizer.decode(decoder.tokenizer.encode(text),{fatal:true}),text);
});
for(const [i,ref] of read('generalization-reference.json').references.entries())test('larger own Transformer matches PyTorch logits '+i,()=>{
 const actual=decoder.logits(ref.tokens);
 assert.ok(Math.max(...actual.map((v,j)=>Math.abs(v-ref.logits[j])))<0.0002);
});
test('own freely generated answers retain basic profile and unsupported-device boundaries',()=>{
 for(const [q,expected] of [['MERは？','TOKYO MERは、鈴木亮平さん主演のTBSの日曜劇場ドラマです。'],['趣味は何？','趣味は写真・映像制作とランニングです。'],['Headphone2の重さは？','その情報は分かりません。']]){
  const answer=decoder.generate(q);assert.equal(answer.text,expected);assert.ok(answer.eos);assert.ok(answer.validTokens);
 }
});
test('non-Wikipedia raw sources retain attribution and page-level holdouts',()=>{
 const sources=read('web-language-sources.json');
 assert.ok(sources.excludedSources.includes('Wikipedia'));
 const documents=fs.readFileSync(new URL('../training/dialogue/web-language-documents.jsonl',import.meta.url),'utf8').trim().split('\n').map(JSON.parse);
 assert.equal(documents.length,50);assert.equal(new Set(documents.map(r=>r.url)).size,documents.length);
 assert.deepEqual([...new Set(documents.map(r=>new URL(r.url).hostname))].sort(),['www.jma.go.jp','www.maff.go.jp']);
 for(const document of documents){
  const source=sources.sources.find(r=>r.url===document.url);assert.ok(source);assert.ok(source.attribution.includes(document.url));
  assert.equal(createHash('sha256').update(document.text).digest('hex'),document.textSha256);assert.equal(source.textSha256,document.textSha256);
  assert.equal(source.license,'公共データ利用規約（第1.0版）');assert.ok(source.modifications);
 }
});
