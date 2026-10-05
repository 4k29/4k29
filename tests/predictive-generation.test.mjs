import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {generationModel as model} from '../docs/generation-model.js';
import {neuralModel} from '../docs/neural-model.js';
import {generationGrammar} from '../docs/generation-grammar.js';
import {nextTokenProbability,predictNextTokens,sequenceLikelihood} from '../docs/next-token-model.js';
import {generateCandidates} from '../docs/predictive-generator.js';
import {naturalGrammarPaths} from '../docs/response-voice.js';
import {trainGeneration} from '../training/train-generation.mjs';
import {Conversation} from '../docs/dialogue.js';
import {LocalLearning} from '../docs/local-learning.js';
import {QuestionJournal,ENGINE_VERSION} from '../docs/question-journal.js';
import {responsePreferences,preferenceRequest} from '../docs/response-preferences.js';
const data=JSON.parse(fs.readFileSync(new URL('../docs/profile.json',import.meta.url)));
test('training is reproducible and learns preference weights from a documented corpus',()=>{
 assert.deepEqual(trainGeneration(),model);
 assert.ok(model.training.paths>=800);assert.ok(model.training.uniquePaths>=700);
 assert.ok(model.training.finalPreferenceLoss<model.training.initialPreferenceLoss*.4);
 assert.ok(model.preferenceWeights.every(w=>Number.isFinite(w)&&w>0));
});
test('next-token distributions normalize and change with preceding words and style',()=>{
 const row=model.paths.find(p=>p.id==='ja:name:polite:normal:0'),context={language:'ja',kind:'name',style:'polite'};
 const sum=model.vocabulary.reduce((s,_,id)=>s+nextTokenProbability(model,context,[0,0,0],id),0);assert.ok(Math.abs(sum-1)<1e-9);
 const before=row.tokens.slice(0,2),next=row.tokens[2];
 assert.ok(nextTokenProbability(model,context,before,next)>nextTokenProbability(model,context,[0,0,0],next));
 const friendly={...context,style:'friendly'},ending=model.vocabulary.indexOf('です');
 assert.ok(nextTokenProbability(model,context,row.tokens.slice(0,3),ending)>nextTokenProbability(model,friendly,row.tokens.slice(0,3),ending));
 const allowed=row.tokens.slice(0,3),predictions=predictNextTokens(model,context,[0,0,0],allowed);
 assert.ok(Math.abs(predictions.reduce((s,p)=>s+p.constrainedProbability,0)-1)<1e-9);
 assert.ok(Number.isFinite(sequenceLikelihood(model,context,row.tokens).meanLogProbability));
});
test('every grammar path preserves exactly one registered value slot',()=>{
 for(const row of generationGrammar){assert.equal((row.template.match(/\{value\}/g)||[]).length,1,row.id);assert.doesNotMatch(row.template,/undefined|NaN|\bi am\b/,row.id);}
 for(const language of ['ja','en'])for(const kind of new Set(model.paths.filter(p=>p.language===language).map(p=>p.kind))){
  const value='REGISTERED_VALUE <script>literal</script>',candidates=generateCandidates(kind,language,{value,label:'REGISTERED_TYPE'},{style:'friendly'});
  assert.ok(candidates.length>=4,language+':'+kind);
  const paths=naturalGrammarPaths(model.paths,model.vocabulary);
  for(const c of candidates){assert.equal(c.text.split(value).length,2);assert.doesNotMatch(c.text,/\{(?:value|label)\}|<eos>|<bos>|undefined|NaN/);assert.ok(paths.some(p=>p.id===c.pathId&&JSON.stringify([...p.tokens,1])===JSON.stringify(c.tokens)));assert.ok(c.transitions>c.tokens.length);}
 }
});
for(const question of ['名前は？','趣味は？','好きな人は？','サブスクは？','ランニングの靴は？','ランニングのアプリは？','記事では何について書いてる？'])test('expanded friendly answers keep evidence and links: '+question,()=>{
 const c=new Conversation(data),answers=Array.from({length:16},()=>c.respond(question));assert.ok(new Set(answers.map(a=>a.text)).size>=(question.includes('趣味')?4:8));
 for(const a of answers){assert.deepEqual(a.factIds,answers[0].factIds);assert.deepEqual(a.links,answers[0].links);assert.equal(a.generation.style,'friendly');assert.equal(a.generation.method,'constrained-next-token');}
});
test('brief and detailed preferences affect wording while preserving all requested facts',()=>{
 for(const question of ['名前は？','趣味は？','制作の流れは？','ランニングの道具は？']){
  const brief=new Conversation(data,{preferences:{length:'brief'}}),detail=new Conversation(data,{preferences:{length:'detail'}});
  const short=Array.from({length:6},()=>brief.respond(question)),long=Array.from({length:6},()=>detail.respond(question));
  assert.deepEqual(short[0].factIds,long[0].factIds);
  assert.ok(short.reduce((s,a)=>s+a.text.length,0)<long.reduce((s,a)=>s+a.text.length,0),question);
 }
});
test('explicit style preferences retain context and can be overridden',()=>{
 const c=new Conversation(data);c.respond('好きな人は？');const ack=c.respond('これからは丁寧な口調で答えて');
 assert.equal(ack.unanswered,false);assert.equal(ack.learningEligible,false);assert.deepEqual(ack.factIds,[]);
 const follow=c.respond('その人のXは？');assert.deepEqual(follow.factIds,['favorite-person']);assert.equal(follow.links[0].url,'https://x.com/popico_pi');assert.equal(follow.generation.style,'polite');
 c.respond('くだけた口調で');assert.equal(c.respond('名前は？').generation.style,'friendly');
 assert.equal(preferenceRequest('今後は簡潔にお願いします').onlyInstruction,true);
 assert.equal(preferenceRequest('親しみやすい、少しくだけた口調').onlyInstruction,true);
});
test('temporary and rejected instructions do not overwrite remembered preferences',()=>{
 const c=new Conversation(data);const a=c.respond('今回は丁寧な口調で名前は？');assert.equal(a.generation.style,'polite');assert.equal(a.preferenceUpdate,null);
 assert.equal(c.respond('名前は？').generation.style,'friendly');
 assert.equal(c.respond('今回は短く答えて').preferenceUpdate,null);assert.equal(c.respond('趣味は？').generation.length,'normal');
 assert.equal(preferenceRequest('短く答えないで').update,null);
 assert.equal(preferenceRequest('use a polite tone, use a casual tone').update.style,'friendly');
 assert.equal(preferenceRequest('briefing').update,null);
});
test('journal reload, review flags and deletion immediately control remembered preferences',()=>{
 const entries=new Map(),storage={getItem:k=>entries.get(k)||null,setItem:(k,v)=>entries.set(k,v),removeItem:k=>entries.delete(k)},journal=new QuestionJournal({storage});
 const create=()=>new Conversation(data,{learner:new LocalLearning(data,()=>journal.records)});let c=create();
 const q='丁寧な口調で答えて',record=journal.add(q,c.respond(q),data.unknownReply);
 assert.equal(create().respond('名前は？').generation.style,'polite');
 assert.equal(new QuestionJournal({storage}).records[0].preferenceUpdate.style,'polite');
 journal.mark(record.id,true);assert.equal(c.respond('名前は？').generation.style,'friendly');
 journal.mark(record.id,false);assert.equal(c.respond('名前は？').generation.style,'polite');
 journal.clear();assert.equal(c.respond('名前は？').generation.style,'friendly');
});
test('ordinary replies, unknown inputs and unverified records do not reinforce style',()=>{
 assert.equal(responsePreferences([{question:'短く答えて',answer:'OK',learningEligible:true}],{style:'friendly'}).length,'normal');
 assert.equal(responsePreferences([{question:'短く答えて',preferenceUpdate:{length:'detail'}}]).length,'normal');
 const c=new Conversation(data);assert.equal(c.respond('くだけた口調で住所は？').text,data.unknownReply);
 assert.equal(c.respond('名前は？').generation.style,'friendly');
 const learner=new LocalLearning(data,()=>[{engine:'obsolete',learningEligible:true,question:'日々の耳元のお供を聞かせて',factIds:['earphones-beats'],intents:['earphones']}]);assert.equal(learner.retrieve('日々の耳元のお供を聞かせて'),null);
 // Intent/classification updates invalidate old journal labels even when the
 // numerical model weights are unchanged.
 const previousEngine=new LocalLearning(data,()=>[{engine:neuralModel.version,learningEligible:true,question:'日々の耳元のお供を聞かせて',factIds:['earphones-beats'],intents:['earphones']}]);
 assert.equal(previousEngine.retrieve('日々の耳元のお供を聞かせて'),null);
 assert.notEqual(ENGINE_VERSION,neuralModel.version);assert.equal(neuralModel.baseVersion,model.version);
});
test('value-only, URL-only and unknown responses bypass predictive wording',()=>{
 const c=new Conversation(data);c.respond('イヤホンは？');const names=c.respond('それの名前だけ');assert.equal(names.generation.method,'registered-value');assert.equal(names.text,names.factIds.map(id=>data.facts.find(f=>f.id===id).ja.value).join('\n'));
 c.respond('サブ垢は？');const url=c.respond('そのリンクだけ');assert.equal(url.text,'https://x.com/uma_4k');assert.equal(url.generation.method,'registered-value');
 for(const q of ['年齢は？','ヘッドホンの値段は？','あなたのYouTubeは？']){const a=c.respond(q);assert.equal(a.text,data.unknownReply);assert.equal(a.generation,null);assert.deepEqual(a.links,[]);}
});
test('quantity words and procedural AI questions cannot become product/tool-only answers',()=>{
 const c=new Conversation(data);assert.deepEqual(c.respond('普段の活動をいくつか教えて').factIds,['tecirc','photo','running']);
 assert.deepEqual(new Set(c.respond('AIを使ってどうやって作ってる？').factIds),new Set(['workflow','iteration','taste']));
});
for(const row of JSON.parse(fs.readFileSync(new URL('../evaluation/prediction.json',import.meta.url))))test('prediction regression: '+row.question,()=>{
 const c=new Conversation(data);for(const q of row.setup||[])c.respond(q);const a=c.respond(row.question);
 assert.deepEqual([...a.factIds].sort(),[...row.facts].sort());if(row.unanswered!==undefined)assert.equal(a.unanswered,row.unanswered);
 if(row.links)assert.deepEqual(a.links.map(l=>l.url).sort(),[...row.links].sort());if(!row.facts.length)assert.equal(a.text,data.unknownReply);
});
test('language evaluation phrases are disjoint from training and get finite predictions',()=>{
 const rows=JSON.parse(fs.readFileSync(new URL('../training/generation-holdout.json',import.meta.url)));assert.equal(rows.length,26);
 for(const row of rows){assert.equal(generationGrammar.some(g=>g.language===row.language&&g.template===row.template),false,row.template);
  assert.ok(Number.isFinite(sequenceLikelihood(model,row,[2,2,2]).meanLogProbability));
 }
});
