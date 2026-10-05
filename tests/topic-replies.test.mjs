import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {Conversation} from '../docs/dialogue.js';
const data=JSON.parse(fs.readFileSync(new URL('../docs/profile.json',import.meta.url)));

test('bare Latin brand and product names answer in Japanese instead of inferring English',()=>{
 for(const q of ['Apple','APPLE?','Nothing','OpenAI','HCI','SLM','kyu','MER','VIVANT','Nothing Headphone (1)']){
  const r=new Conversation(data).respond(q);assert.equal(r.language,'ja',q);
  assert.match(r.text,/[ぁ-んァ-ヶ一-龠]/,q);assert.doesNotMatch(r.text,/I'm drawn|I am drawn/,q);
 }
 const apple=new Conversation(data).respond('Apple');assert.deepEqual(apple.factIds,['apple']);assert.match(apple.text,/Apple.*(?:関心|興味|気にな)/);
});

test('explicit English questions and their bare-topic follow-ups preserve English',()=>{
 const c=new Conversation(data);assert.equal(c.respond('What are your interests?').language,'en');
 assert.equal(c.respond('Apple').language,'en');
 assert.equal(c.respond('何に興味がある？').language,'ja');assert.equal(c.respond('Apple').language,'ja');
});

test('interest-only subjects never appear in general favorites, including after an interest answer',()=>{
 const c=new Conversation(data);const interests=c.respond('興味のあるものは何？');
 for(const id of ['hci','slm','context'])assert.ok(interests.factIds.includes(id));
 for(const q of ['好きなものは何','好きなものは？','何が好き？','What do you like?']){
  const r=c.respond(q);for(const id of ['hci','slm','context'])assert.ok(!r.factIds.includes(id),q);
  for(const id of ['apple','nothing','openai','tech','ui','design','favorite-vivant','favorite-kyu','favorite-tokyo-mer','favorite-person'])assert.ok(r.factIds.includes(id),q);
  assert.doesNotMatch(r.text,/HCI|小規模言語モデル|人や状況に合わせた情報体験/);
 }
});

test('named headphone detail requests return connected specifications rather than an ownership sentence',()=>{
 for(const q of ['Nothing Headphone (1)について詳しく教えて','nothing headphone1を詳しく説明して','Headphone(1)の特徴を詳しく教えて','詳しく答えて、Nothing Headphone (1)','Tell me about Nothing Headphone (1) in detail']){
  const r=new Conversation(data).respond(q);assert.equal(r.unanswered,false,q);
  assert.ok(r.factIds.every(id=>id.startsWith('specification:headphones:')),q);
  assert.match(r.text,/40mm/);assert.match(r.text,/5\.3/);assert.match(r.text,/IP52/);assert.match(r.text,/329g/);
  assert.doesNotMatch(r.text,/を使っている|を使っています|を使う|I use/);
 }
});

test('asking for more after a named headphone answer expands that product and keeps conditions',()=>{
 const c=new Conversation(data);c.respond('Nothing Headphone (1)は使ってる？');const r=c.respond('もっと詳しく教えて');
 assert.ok(r.factIds.every(id=>id.startsWith('specification:headphones:')));assert.match(r.text,/透明なイヤーカップ/);
 assert.match(r.text,/AAC・ANCオン.*35時間/);assert.match(r.text,/LDAC・ANCオン.*30時間/);
 assert.doesNotMatch(r.text,/Beats Fit Pro|CMF Buds/);
});

test('product detail expansion retains brand introductions and unknown model/ownership guards',()=>{
 const kyu=new Conversation(data).respond('kyuについて詳しく教えて');assert.deepEqual(kyu.factIds,['favorite-kyu']);assert.match(kyu.text,/ブランド/);
 for(const q of ['Nothing Headphone (2)について詳しく教えて','CMF Buds Pro 5について詳しく教えて','友達のヘッドホンについて詳しく教えて','Nothing Headphone (1)を買った理由を詳しく教えて']){
  const r=new Conversation(data).respond(q);assert.equal(r.unanswered,true,q);assert.deepEqual(r.factIds,[],q);
 }
});
