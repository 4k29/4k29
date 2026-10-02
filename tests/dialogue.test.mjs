import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {Conversation} from '../docs/dialogue.js';
import {deviceInfo} from '../docs/boot.js';
const data=JSON.parse(fs.readFileSync(new URL('../docs/profile.json',import.meta.url)));
test('facts, follow-up context, variation and reset',()=>{
 const c=new Conversation(data);
 assert.match(c.respond('名前は？').text,/4k29/);
 const first=c.respond('興味は？').text;
 const next=c.respond('もっと').text;
 assert.notEqual(first,next);assert.ok(c.lastTopics.includes('interests'));
 assert.match(c.respond('愛用製品は？').text,/Nothing Headphone \(1\)/);
 assert.match(c.respond('Xは？').text,/@p_horeer/);
 assert.match(c.respond('写真とランニングは？').text,/写真|ランニング/);
 assert.match(c.respond('開発スタイルは？').text,/ChatGPT|Codex|プレビュー/);
 c.reset();assert.equal(c.history.length,0);assert.deepEqual(c.lastTopics,[]);
});
test('unregistered details and unexpected questions cannot create facts',()=>{
 const c=new Conversation(data);
 for(const q of ['何歳？','どこの学校？','なぜNothingが好き？','明日の天気は？','メールアドレスは？'])assert.match(c.respond(q).text,/登録されていない|登録されていません/);
 assert.match(c.respond('What is your birthday?').text,/not registered/);
 assert.match(c.respond('<script>alert(1)</script>').text,/registered information/);
});
test('answers are assembled from editable facts',()=>{
 const clone=structuredClone(data);clone.facts.find(f=>f.id==='name').ja.value='テスト名';
 assert.match(new Conversation(clone).respond('名前は？').text,/テスト名/);
 const c=new Conversation(data);assert.notEqual(c.respond('design').text,c.respond('design').text);
});
test('device capabilities are reported without user-agent inference',()=>{
 const unknown=deviceInfo({userAgent:'Mozilla Safari Windows'}, {}, {});
 assert.equal(unknown.OS,'Unknown');assert.equal(unknown.Browser,'Unknown');assert.equal(unknown.Device,'Unknown');assert.equal(unknown.Screen,'Unknown');
 const known=deviceInfo({language:'ja-JP',languages:['ja-JP'],userAgentData:{platform:'Windows',mobile:false,brands:[{brand:'Chromium',version:'153'}]}},{width:390,height:844},{innerWidth:390,innerHeight:700});
 assert.equal(known.OS,'Windows');assert.equal(known.Screen,'390 × 844');assert.equal(known.Language,'ja-JP');assert.match(known.Browser,/Chromium/);
});
test('all local assets exist and all profile facts have provenance',()=>{
 for(const f of data.facts){assert.ok(f.source);assert.ok(f.ja.value);assert.ok(f.en.value);}
 const html=fs.readFileSync(new URL('../docs/index.html',import.meta.url),'utf8');
 for(const match of html.matchAll(/(?:src|href)="(\.\/[^\"]+)"/g))assert.ok(fs.existsSync(new URL('../docs/'+match[1].slice(2),import.meta.url)));
});
