import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {Conversation} from '../docs/dialogue.js';
const data=JSON.parse(fs.readFileSync(new URL('../docs/profile.json',import.meta.url)));
const cases=[
 ['何のイヤホン使ってる',['earphones-beats','earphones-cmf']],
 ['なんのいやほんつかってる',['earphones-beats','earphones-cmf']],
 ['ヘッドホンは？',['headphones']],
 ['へっどほんはなに',['headphones']],
 ['契約してるサブスクは？',['subscription-chatgpt','subscription-apple','subscription-icloud']],
 ['けいやくしてるさぶすくは',['subscription-chatgpt','subscription-apple','subscription-icloud']],
 ['推しは誰？',['favorite-person']],
 ['おしはだれ',['favorite-person']],
 ['あなたのなまえは',['name']],
 ['しゅみはなに',['tecirc','web','photo','running']],
 ['さぶあかは',['x-secondary']],
 ['どういう風に開発してるの',['workflow','iteration','taste']],
 ['普段どんな技術を使ってる',['workflow']],
];
for(const [q,ids] of cases)test('user question: '+q,()=>{
 const a=new Conversation(data).respond(q);assert.deepEqual(new Set(a.factIds),new Set(ids));
 for(const id of ids)assert.ok(a.text.includes(data.facts.find(f=>f.id===id).ja.value));
});
test('product name follow-up preserves product type',()=>{
 const c=new Conversation(data);c.respond('イヤホンは？');const a=c.respond('それの名前だけ');
 assert.deepEqual(a.factIds,['earphones-beats','earphones-cmf']);assert.doesNotMatch(a.text,/4k29|Headphone/);
});
test('subscriptions never resolve to subaccount and retain supplied capacity',()=>{
 const a=new Conversation(data).respond('サブスクは？');assert.match(a.text,/250GB/);assert.doesNotMatch(a.text,/@|uma_4k|p_horeer/);
});
test('unsupported subscription and attributes are not inferred',()=>{
 for(const q of ['Netflix契約してる？','イヤホンの値段は？','推しの本名は？','おしえて','私のイヤホンは？'])assert.equal(new Conversation(data).respond(q).text,data.unknownReply,q);
});
test('supplied facts remain editable independently of the engine',()=>{
 const clone=structuredClone(data);clone.facts.find(f=>f.id==='earphones-beats').ja.value='交換したイヤホン';
 assert.match(new Conversation(clone).respond('イヤホンは？').text,/交換したイヤホン/);
});

test('similar-question retrieval rejects unsupported subjects',async()=>{
 const {retrieveIntent}=await import('../docs/intent-retrieval.js');
 for(const q of ['宇宙について説明して','犬の名前は','夕飯は何食べた','ゲームの攻略法は'])assert.equal(retrieveIntent(q),null,q);
});
test('additional interests stay in the same topic instead of implying ownership',()=>{
 const c=new Conversation(data);c.respond('興味は？');const a=c.respond('もっと');assert.ok(a.factIds.length);assert.ok(a.factIds.every(id=>data.facts.find(f=>f.id===id).topic==='interests'));
});


test('removed weather and web-search requests do not return unrelated profile facts or links',()=>{
 for(const q of ['今日の天気は？','東京の天気','OpenAIを検索して','検索: Apple']){const a=new Conversation(data).respond(q);assert.equal(a.text,data.unknownReply,q);assert.deepEqual(a.links,[]);}
});
