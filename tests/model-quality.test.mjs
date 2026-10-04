import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {Conversation} from '../docs/dialogue.js';
const data=JSON.parse(fs.readFileSync(new URL('../docs/profile.json',import.meta.url)));
const cases=JSON.parse(fs.readFileSync(new URL('../evaluation/quality.json',import.meta.url)));
for(const row of cases)test('model quality: '+[...(row.setup||[]),row.question].join(' → '),()=>{
 const c=new Conversation(data);for(const question of row.setup||[])c.respond(question);
 const a=c.respond(row.question);
 assert.deepEqual(new Set(a.factIds),new Set(row.facts));assert.equal(a.unanswered,row.unanswered);
 if(row.links)assert.deepEqual(a.links.map(l=>l.url).sort(),[...row.links].sort());
 if(!row.facts.length){assert.equal(a.text,data.unknownReply);assert.deepEqual(a.links,[]);}
});
test('audio categories and distinct question order remain clear in the composed answer',()=>{
 const a=new Conversation(data).respond('イヤホンと職業とヘッドホンは？');
 assert.deepEqual(a.factIds,['earphones-beats','earphones-cmf','headphones','student']);
 assert.match(a.text,/イヤホン/);assert.match(a.text,/ヘッドホン/);
 assert.ok(a.text.indexOf('Beats Fit Pro')<a.text.indexOf('学生'));
 assert.ok(a.text.indexOf('Nothing Headphone (1)')<a.text.indexOf('学生'));
});
test('context resolves a requested value without turning it into a standalone learning example',()=>{
 const c=new Conversation(data);c.respond('サブスクは？');const a=c.respond('名前だけ教えて');
 assert.equal(a.text,data.facts.filter(f=>f.topic==='subscriptions').map(f=>f.ja.value).join('\n'));
 assert.equal(a.learningEligible,false);
 c.reset();assert.deepEqual(c.respond('名前だけ教えて').factIds,['name']);
});
test('deleting registered facts immediately removes contextual results and their links',()=>{
 const clone=structuredClone(data);clone.facts=clone.facts.filter(f=>f.id!=='favorite-person'&&f.id!=='running-app');
 const c=new Conversation(clone);c.respond('ランニングは？');assert.deepEqual(c.respond('アプリは？').factIds,[]);
 c.respond('推しは？');assert.deepEqual(c.respond('その人のXは？').links,[]);
});
test('an article location follow-up keeps the selected article, while a new subject changes it',()=>{
 const c=new Conversation(data),first=c.respond('iPhone eの記事を読みたい');
 const follow=c.respond('どこで読める？');assert.deepEqual(follow.factIds,first.factIds);assert.deepEqual(follow.links,first.links);assert.equal(follow.learningEligible,false);
 const changed=c.respond('Where can I read your iPhone Duo article?');
 assert.ok(changed.factIds.length>0);
 assert.notDeepEqual(changed.factIds,first.factIds);
 assert.ok(changed.factIds.every(id=>data.facts.find(f=>f.id===id).lookupTerms?.some(term=>/duo/i.test(term))));
});
