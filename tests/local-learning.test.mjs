import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {LocalLearning} from '../docs/local-learning.js';import {Conversation} from '../docs/dialogue.js';import {QuestionJournal} from '../docs/question-journal.js';
const data=JSON.parse(fs.readFileSync(new URL('../docs/profile.json',import.meta.url)));
const example={question:'日々の耳元のお供を聞かせて',factIds:['earphones-beats','earphones-cmf'],intents:['earphones'],learningEligible:true};
// Use actual IDs from the editable profile, rather than any answer text.
example.factIds=data.facts.filter(f=>f.category==='earphones').map(f=>f.id);
test('local examples recognize a close new phrasing and regenerate registered facts',()=>{
 const learner=new LocalLearning(data,()=>[example]);const query='日々の耳元のお供を教えて';
 assert.deepEqual(learner.retrieve(query).factIds,example.factIds);
 const answer=new Conversation(data,{learner}).respond(query);assert.equal(answer.learned,true);assert.match(answer.text,/Beats Fit Pro/);assert.match(answer.text,/CMF Buds/);assert.equal(answer.learningEligible,false);
});
test('review flags, deletion, missing facts and unknown answers immediately stop learning',()=>{
 let records=[{...example}];const learner=new LocalLearning(data,()=>records);assert.ok(learner.retrieve(example.question));
 for(const change of [{needsReview:true},{unanswered:true},{learned:true},{learningEligible:false},{factIds:['web']}]){records=[{...example,...change}];assert.equal(learner.retrieve(example.question),null);}
 records=[];assert.equal(learner.retrieve(example.question),null);
});
test('ambiguous labels and insufficient similarity abstain',()=>{
 const learner=new LocalLearning(data,()=>[example,{...example,factIds:['name']}]);assert.equal(learner.retrieve(example.question),null);
 const other=new LocalLearning(data,()=>[example]);for(const q of ['耳元','明日の天気は？','日々の耳元のお供はいくらなの'])assert.equal(other.retrieve(q),null,q);
});
test('learned examples never bypass missing-attribute guards or search prohibition',()=>{
 const records=['年齢は？','ランニングはどこ走る？','検索して','Web開発は何をしている？'].map(question=>({...example,question,factIds:['name']}));
 const conversation=new Conversation(data,{learner:new LocalLearning(data,()=>records)});
 for(const r of records)assert.equal(conversation.respond(r.question).text,data.unknownReply,r.question);
});
test('only independent strong answers are eligible and survive journal reload',()=>{
 const values=new Map(),storage={getItem:k=>values.get(k),setItem:(k,v)=>values.set(k,v)};const journal=new QuestionJournal({storage});const c=new Conversation(data);
 const answer=c.respond('何のイヤホン使ってる？');assert.equal(answer.learningEligible,true);journal.add('何のイヤホン使ってる？',answer,data.unknownReply);
 const loaded=new QuestionJournal({storage});assert.equal(new LocalLearning(data,()=>loaded.records).examples().length,1);
 assert.equal(c.respond('それの名前は？').learningEligible,false);assert.equal(c.respond('名前と年齢は？').learningEligible,false);
});
