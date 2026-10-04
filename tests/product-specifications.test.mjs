import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {Conversation} from '../docs/dialogue.js';
import {specificationMemory,recallSpecification} from '../docs/product-specifications.js';
const data=JSON.parse(fs.readFileSync(new URL('../docs/profile.json',import.meta.url)));
const ask=(q,setup=[])=>{const c=new Conversation(data);for(const s of setup)c.respond(s);return c.respond(q);};
test('literal numerical facts are genuinely recalled from learned weights in both languages',()=>{
 const source=fs.readFileSync(new URL('../training/product-specifications.json',import.meta.url));
 assert.equal(specificationMemory.sourceSha256,createHash('sha256').update(source).digest('hex'));
 let count=0;
 for(const p of specificationMemory.products)for(const f of p.fields)for(const lang of ['ja','en']){
  const r=recallSpecification(f,lang);assert.equal(r.exact,true,p.id+':'+f.key+':'+lang);assert.equal(r.text,f[lang].value);count++;
 }
 for(const d of specificationMemory.descriptions)for(const lang of ['ja','en']){
  const r=recallSpecification(d,lang,'favorite');assert.equal(r.exact,true,d.id+':'+lang);assert.equal(r.text,d[lang]);count++;
 }
 assert.equal(count,70);
});
test('battery answers distinguish ANC, codecs and charging cases',()=>{
 const cmf=ask('CMF BudsのANCオンの電池は？');assert.match(cmf.text,/単体最大5\.6時間、ケース込み最大24時間/);
 const off=ask('CMF BudsのANCオフの再生時間は？');assert.match(off.text,/最大8時間.*最大35\.5時間/);
 const h=ask('Headphone1のLDAC・ANCオンのバッテリーは？');assert.match(h.text,/最大30時間/);assert.doesNotMatch(h.text,/35時間|54時間|80時間/);
 const a=ask('Nothing Headphone(1)のAAC・ANCオフの再生時間');assert.match(a.text,/最大80時間/);assert.doesNotMatch(a.text,/35時間|30時間|54時間/);
});
test('case-insensitive product aliases tolerate omitted spaces and parentheses',()=>{
 for(const name of ['NOTHING HEADPHONE (1)','nothing headphone(1)','Nothing Headphone1','headphone 1','Headphone（1）']){
  const a=ask(name+'の重さは？');assert.deepEqual(a.factIds,['specification:headphones:weight']);assert.match(a.text,/329g/);
 }
});
test('generic audio specifications include both categories with their names',()=>{
 for(const q of ['イヤホンのスペックは？','ヘッドホンの仕様は？']){
  const a=ask(q);for(const name of ['イヤホン','ヘッドホン','Beats Fit Pro','CMF Buds','Nothing Headphone (1)'])assert.ok(a.text.includes(name));
  assert.equal(a.unanswered,false);assert.ok(a.links.every(l=>/^https:\/\/(support\.(?:apple\.com|cmf\.tech)|jp\.nothing\.tech)\//.test(l.url)));
 }
});
test('follow-ups select the previous product; unsupported personal attributes stay unknown',()=>{
 const a=ask('それのBluetoothは？',['CMF Budsのスペック']);assert.deepEqual(a.factIds,['specification:earphones-cmf:bluetooth']);assert.match(a.text,/5\.3/);
 for(const q of ['私のイヤホンのスペックは？','友達のヘッドホンの重さは？','CMF Buds Proのバッテリーは？','CMF Buds 2の防水は？','Nothing Headphone (a)の重さは？','Nothing Headphone (1)をいくらで買った？','kyu cameraは使ってる？'])assert.equal(ask(q).text,data.unknownReply,q);
});
test('liked camera specifications do not assert ownership; conflicted Beats totals stay unasserted',()=>{
 const k=ask('kyu cameraのスペック');assert.match(k.text,/32GB/);assert.match(k.text,/115g/);assert.doesNotMatch(k.text,/使っている|持っている|買った/);
 assert.equal(ask('Beats Fit Proの再生時間は？').text,data.unknownReply);
 const b=ask('Beats Fit Proの耐水性能は？');assert.match(b.text,/IPX4/);assert.match(b.text,/ケースは非対応/);
 assert.doesNotMatch(b.text,/はイヤホン本体は|はANCに対応だよ/);
});
test('a rating for earbuds cannot be presented as a charging-case rating',()=>{
 assert.equal(ask('CMF Budsのケースは防水？').text,data.unknownReply);
 assert.equal(ask('Nothing Headphone (1)のケースの耐水性能は？').text,data.unknownReply);
 assert.match(ask('Beats Fit Proのケースは防水？').text,/ケースは非対応/);
});
test('a dual Bluetooth connection question asks about device count rather than version',()=>{
 const a=ask('CMF BudsはBluetoothで2台同時接続できますか？');assert.deepEqual(a.factIds,['specification:earphones-cmf:multipoint']);assert.match(a.text,/2台同時接続.*Nothing X/);
 const b=ask('Headphone 1はBluetoothで2台同時接続できますか？');assert.deepEqual(b.factIds,['specification:headphones:multipoint']);assert.match(b.text,/2台同時接続に対応/);
});
test('product specifications form a readable paragraph without repeated model names',()=>{
 const a=ask('Headphone (1)のスペックは');
 assert.equal(a.text.split('Nothing Headphone (1)').length-1,1);
 assert.match(a.text,/Nothing.*ヘッドホン/);assert.match(a.text,/透明なイヤーカップ/);
 assert.match(a.text,/40mm.*Bluetooth 5\.3.*IP52/);
 assert.equal(a.text.includes('\n'),false);assert.equal(a.text.split('。').filter(Boolean).length,2);
 assert.doesNotMatch(a.text,/だよ。|のドライバーは|のBluetoothは/);
 const detail=ask('Nothing Headphone1のスペックを詳しく');assert.match(detail.text,/329g.*16Ω/);assert.match(detail.text,/AAC・ANCオン.*35時間.*LDAC・ANCオン.*30時間/);
});
