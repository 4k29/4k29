import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {Conversation} from '../docs/dialogue.js';
const read=p=>JSON.parse(fs.readFileSync(new URL(p,import.meta.url)));
const data=read('../docs/profile.json'),cases=read('../evaluation/favorites.json');
for(const row of cases)test('favorite question: '+row.question,()=>{
 const c=new Conversation(data);for(const q of row.setup||[])c.respond(q);
 const a=c.respond(row.question);
 assert.deepEqual(new Set(a.factIds),new Set(row.facts));
 if(row.links)assert.deepEqual(new Set(a.links.map(l=>l.url)),new Set(row.links));
 if(row.unanswered)assert.equal(a.text,data.unknownReply);
 assert.doesNotMatch(a.text,/と述べ|挙げています|本人は|プロフィールに|登録されています/);
});
test('brief introductions, detailed context and name-only replies answer different needs',()=>{
 const c=new Conversation(data),short=c.respond('TOKYO MERについて教えて'),detail=c.respond('もっと詳しく');
 assert.match(short.text,/TBSの日曜劇場/);
 assert.match(detail.text,/鈴木亮平/);assert.doesNotMatch(detail.text,/喜多見幸太|手術室|ERカー/);
 assert.deepEqual(detail.factIds,short.factIds);
 const names=c.respond('名前だけ');assert.equal(names.text,'TOKYO MER');assert.deepEqual(names.links,[]);
});
test('brand and drama introductions retain the supplied identity and public source',()=>{
 const kyu=new Conversation(data).respond('kyuについて教えて');
 assert.match(kyu.text,/カメラとアプリ/);assert.match(kyu.text,/機能を意図的に絞/);
 assert.doesNotMatch(kyu.text,/使っている|持っている|買った/);
 assert.equal(kyu.links[0].url,'https://kyu-core.com/');
 const mer=new Conversation(data).respond('TOKYO MERについて教えて');
 assert.match(mer.text,/鈴木亮平/);assert.match(mer.text,/TBSの日曜劇場/);assert.match(mer.text,/ドラマ/);
 assert.doesNotMatch(mer.text,/映画/);
});
test('generic favorites preserve all existing interests and the creator',()=>{
 const a=new Conversation(data).respond('好きなものは？');
 const expected=data.facts.filter(f=>f.ja.relation==='interest'||f.ja.relation==='favoriteThing'||f.id==='favorite-person').map(f=>f.id);
 assert.deepEqual(new Set(a.factIds),new Set(expected));
 assert.deepEqual(a.text.split("\n"),a.factIds.map(id=>(data.facts.find(f=>f.id===id).ja.shortName||data.facts.find(f=>f.id===id).ja.value)));assert.doesNotMatch(a.text,/アオのハコ/);assert.match(a.text,/してはる/);
});
test('bare MER and VIVANT questions begin with the description instead of a favorite announcement',()=>{
 for(const q of ['merは？','MERは？','VIVANTは？','kyuは？']){
  const a=new Conversation(data).respond(q);assert.equal(a.unanswered,false);assert.doesNotMatch(a.text,/好きな(?:ドラマ|ブランド|もの)は/);
 }
 const mer=new Conversation(data).respond('merは？');assert.match(mer.text,/^TOKYO MERは、鈴木亮平さん主演のTBSの日曜劇場/);
});
test('audio answers omit explanatory filler while keeping both device categories',()=>{
 const c=new Conversation(data);for(let i=0;i<16;i++){
  const a=c.respond('なんのイヤホン使ってる？');assert.doesNotMatch(a.text,/については|として|が普段の|を普段の/);
  for(const name of ['イヤホン','ヘッドホン','Beats Fit Pro','CMF Buds','Nothing Headphone (1)'])assert.ok(a.text.includes(name));
 }
});
test('repeated answers stay in the first person and preserve audio categories',()=>{
 for(const q of ['名前は？','趣味は？','好きなドラマは？','好きなブランドは？','イヤホンは？','ヘッドホンは？']){
  const c=new Conversation(data);
  for(let i=0;i<16;i++){
   const a=c.respond(q);assert.doesNotMatch(a.text,/と述べ|本人は|挙げています|プロフィールでは|登録されています/);
   if(/ホン/.test(q)){assert.match(a.text,/イヤホン/);assert.match(a.text,/ヘッドホン/);assert.match(a.text,/Beats Fit Pro/);assert.match(a.text,/CMF Buds/);assert.match(a.text,/Nothing Headphone \(1\)/);}
  }
 }
});
test('friendly answers use complete natural sentences without obligatory yo endings',()=>{
 const c=new Conversation(data);
 for(const q of ['merは？','趣味は何','なんのイヤホン使ってる？','VIVANTについて','Headphone (1)のスペックは']){
  const a=c.respond(q);assert.equal(a.unanswered,false);assert.doesNotMatch(a.text,/だよ。|ているよ。|については|ヘッドホンとして/);
 }
});
