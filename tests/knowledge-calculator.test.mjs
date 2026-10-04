import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {Conversation} from '../docs/dialogue.js';
const data=JSON.parse(fs.readFileSync(new URL('../docs/profile.json',import.meta.url)));
const examples=[
 ['好きな作品は？',['favorite-vivant','favorite-tokyo-mer'],/VIVANT|TOKYO MER/],
 ['普段どんなドラマを見る？',['favorite-vivant','favorite-tokyo-mer'],/TOKYO MER/],
 ['VIVANTの主演は？',['favorite-vivant'],/主演は堺雅人/],
 ['TOKYO MERの主演は誰？',['favorite-tokyo-mer'],/主演は鈴木亮平/],
 ['音楽を聴く機器は？',['earphones-beats','earphones-cmf','headphones'],/Beats Fit Pro/],
 ['入ってる有料プランは？',['subscription-chatgpt','subscription-apple','subscription-icloud'],/250GB/],
 ['ランニングの記録はどうしてる？',['running-app'],/Nike Run Club/],
 ['コードはどう用意してる？',['workflow','iteration','taste'],/ChatGPT/],
 ['HTMLとは何？',['knowledge-html'],/マークアップ/],
 ['JSONを説明して',['knowledge-json'],/データ/],
 ['Transformerとは？',['knowledge-transformer'],/Attention/],
 ['UIとUXの違いは？',['knowledge-ui','knowledge-ux'],/体験全体/],
 ['空はなぜ青い？',['knowledge-sky'],/短い波長|散乱/],
 ['月はなぜ形が変わる？',['knowledge-moon'],/見る角度/],
 ['なぜ季節があるの？',['knowledge-seasons'],/地軸/],
 ['What is an API?',['knowledge-api'],/interface/]
];
for(const [question,ids,content] of examples)test('broader grounded answer: '+question,()=>{
 const a=new Conversation(data).respond(question);assert.deepEqual(new Set(a.factIds),new Set(ids));assert.equal(a.unanswered,false);assert.match(a.text,content);
});
test('public definitions preserve privacy boundaries and contextual explanations',()=>{
 for(const q of ['あなたの趣味は？','私の年齢は？','私の学校は？'])assert.ok(!new Conversation(data).respond(q).factIds.some(id=>id.startsWith('knowledge-')));
 const c=new Conversation(data);c.respond('HTMLとは？');const a=c.respond('もっと詳しく');assert.deepEqual(a.factIds,['knowledge-html']);assert.match(a.text,/タグ/);assert.equal(a.links[0].url,'https://developer.mozilla.org/en-US/docs/Web/HTML');
 assert.doesNotMatch(new Conversation(data).respond('好きなものは？').text,/アオのハコ/);
});
const calculations=[['2+3*4','14'],['(2+3)*4','20'],['-2^2','-4'],['2^-2','0.25'],['2^3^2','512'],['0.1+0.2','0.3'],['2kmは何m？','2000m'],['90分を時間に','1.5時間'],['1200の15%は？','180'],['平均 2,4,9','5'],['中央値 1,2,100','2']];
for(const [question,value] of calculations)test('calculated answer: '+question,()=>{
 const a=new Conversation(data).respond(question);assert.equal(a.unanswered,false);assert.ok(a.factIds[0].startsWith('calculation-'));assert.ok(a.text.endsWith(value),a.text);
});
test('math parser reports invalid operations and never executes code',()=>{
 assert.match(new Conversation(data).respond('1/0').text,/0で割る|Division by zero/);
 assert.match(new Conversation(data).respond('1mをkgに').text,/同じ種類/);
 assert.equal(new Conversation(data).respond('1+globalThis.process.exit()').text,data.unknownReply);
 const c=new Conversation(data);for(let i=1;i<=100;i++)assert.ok(c.respond(`${i}+${i}*2`).text.endsWith(String(i*3)));
});
