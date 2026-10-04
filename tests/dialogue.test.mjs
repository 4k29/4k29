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
 for(const q of ['何歳？','どこの学校？','なぜNothingが好き？','明日の天気は？','メールアドレスは？'])assert.equal(c.respond(q).text,'すみません、よく分かりません');
 assert.equal(c.respond('What is your birthday?').text,'すみません、よく分かりません');
 assert.equal(c.respond('<script>alert(1)</script>').text,'すみません、よく分かりません');
});
test('answers are assembled from editable facts',()=>{
 const clone=structuredClone(data);clone.facts.find(f=>f.id==='name').ja.value='テスト名';
 assert.match(new Conversation(clone).respond('名前は？').text,/テスト名/);
 const c=new Conversation(data);assert.notEqual(c.respond('design').text,c.respond('design').text);
});
test('device capabilities stay Unknown without structured browser identifiers',()=>{
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

test('main and secondary accounts carry clickable metadata and stay on topic',()=>{
 const c=new Conversation(data);
 const both=c.respond('Twitterのアカウント教えて');
 assert.match(both.text,/@p_horeer/);assert.match(both.text,/@uma_4k/);
 assert.deepEqual(both.links.map(l=>l.url),['https://x.com/p_horeer','https://x.com/uma_4k']);
 for(const question of ['サブ垢は？','別垢ある？','uma_4kについて','alt account']){
  const sub=c.respond(question);assert.match(sub.text,/@uma_4k/);assert.doesNotMatch(sub.text,/@p_horeer/);assert.equal(sub.links[0].url,'https://x.com/uma_4k');
 }
 for(let i=0;i<6;i++)assert.match(c.respond('メインアカウントは？').text,/@p_horeer/);
 assert.deepEqual(new Set(c.respond('名前と趣味は？').topics),new Set(['identity','activities']));
});
test('personal-question paraphrases resolve to registered facts',()=>{
 const cases=[
  ['なんて呼べばいい？',/4k29/],['ニックネームは？',/4k29/],['職業は？',/学生/],['何してる人？',/学生/],
  ['どんな人ですか？',/4k29/],['趣味を教えて',/ランニング/],['休日にすることは？',/写真/],['ジョギングする？',/ランニング/],
  ['スポーツやる？',/ランニング/],['撮影するの？',/写真/],['動画も作る？',/映像/],['記事を書いてる？',/Tecirc/],
  ['ブログどこで読める？',/Tecirc/],['Tecircって何？',/記事/],['どんな記事を書く？',/テクノロジー/],
  ['好きなメーカーは？',/Apple/],['アップルに興味ある？',/Apple/],['ナッシングは好き？',/Nothing/],['オープンAIに関心ある？',/OpenAI/],
  ['ガジェットに興味ある？',/テクノロジー/],['HCIに興味ある？',/HCI/],['小さい言語モデルに興味ある？',/小規模言語モデル/],
  ['愛用のヘッドフォンは？',/Nothing Headphone/],['お気に入りの製品は？',/Nothing Headphone/],
  ['どうやって作るの？',/ChatGPT/],['AIツールは何を使う？',/ChatGPT/],['本人の役割は？',/アイデア/],
  ['デザインで大切なことは？',/初期設定/],['余白へのこだわりは？',/余白/],
  ['このサイトは何の言語で実装？',/HTML/],['このチャットの仕組みは？',/JavaScript/],['プライバシーは？',/外部には?(?:送信しません|送らない|送りません)/],
  ['ツイッターは？',/@p_horeer/],['フォローしたい',/@uma_4k/]
 ];
 for(const [question,pattern] of cases)assert.match(new Conversation(data).respond(question).text,pattern,question);
});
test('unknown details do not inherit a known topic or an unrelated prior answer',()=>{
 const c=new Conversation(data);c.respond('ランニングする？');
 for(const q of ['ランニングの距離は？','どんなカメラを使ってる？','Appleの製品は何を持ってる？','好きな音楽は？','何年生？','何県に住んでる？','誕生日は？'])assert.equal(c.respond(q).text,'すみません、よく分かりません',q);
 assert.equal(c.respond('それについて詳しく').text,'すみません、よく分かりません');
});
