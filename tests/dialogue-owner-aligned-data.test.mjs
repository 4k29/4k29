import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {createTokenizer} from '../training/dialogue/tokenizer.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL('../training/dialogue/'+name,import.meta.url)));
const c=read('owner-aligned-corpus.json'),old=read('switch-corpus.json'),manifest=read('owner-aligned-data.json'),t=createTokenizer(c.tokenizer);
const normal=s=>s.normalize('NFKC').toLowerCase();
const hash=s=>createHash('sha256').update(s).digest('hex');

test('own continuation preserves its training-only vocabulary and immutable declared source identity',()=>{
 assert.deepEqual(c.tokenizer,old.tokenizer);assert.equal(c.provenance.parentCorpusSha256,old.sourceSha256);
 const raw=fs.readFileSync(new URL('../training/dialogue/owner-aligned-corpus.json',import.meta.url),'utf8').trim().replace(/,"sourceSha256":"[0-9a-f]{64}"\}$/, '}');
 assert.equal(hash(raw),c.sourceSha256);assert.equal(manifest.sourceSha256,c.sourceSha256);
 const groups=new Map(),questions=new Map();
 for(const r of c.rows){
  assert.ok(!groups.has(r.group)||groups.get(r.group)===r.partition);groups.set(r.group,r.partition);
  const q=normal(r.question);assert.ok(!questions.has(q)||questions.get(q)===r.partition);questions.set(q,r.partition);
  assert.ok(r.tokens.length<c.provenance.context);assert.ok(Number.isFinite(r.weight)&&r.weight>0);
  assert.equal(t.decode(r.tokens.slice(r.prefixLength,-1),{fatal:true}),r.answer);
 }
 const selection=read('owner-aligned-validation-selection.json'),ids=new Set(c.rows.filter(r=>r.partition==='validation').map(r=>r.id));
 assert.equal(selection.ids.length,256);assert.equal(hash(JSON.stringify(selection.ids)),selection.idsSha256);assert.ok(selection.ids.every(id=>ids.has(id)));
});

test('current profile favorites, interests and complete detail labels are learned as distinct intents',()=>{
 const profile=JSON.parse(fs.readFileSync(new URL('../docs/profile.json',import.meta.url)));
 assert.equal(hash(fs.readFileSync(new URL('../docs/profile.json',import.meta.url))),c.provenance.currentProfileSha256);
 const facts=new Map(profile.facts.map(f=>[f.id,f]));assert.equal(manifest.favoriteFactIds.length,10);
 for(const id of ['hci','slm','context']){assert.equal(facts.get(id).interestOnly,true);assert.ok(!manifest.favoriteFactIds.includes(id));assert.ok(manifest.interestFactIds.includes(id));}
 for(const r of c.rows){
  if(r.intent==='favorites'){assert.equal(r.answer,manifest.targets.favorites);assert.equal(r.factIds.length,10);}
  if(r.intent==='interests')assert.equal(r.answer,manifest.targets.interests);
  if(r.intent==='headphone-spec'){
   assert.equal(r.answer,manifest.targets['headphone-spec']);assert.match(r.answer,/透明なイヤーカップ/);assert.match(r.answer,/40mm.*Bluetooth 5\.3.*AAC・SBC・LDAC.*IP52/);
   assert.match(r.answer,/AAC接続でANCオン35時間・オフ80時間、LDAC接続でオン30時間・オフ54時間/);assert.doesNotMatch(r.answer,/を使っている|だよ/);
  }
  if(r.intent==='headphone-brief'){assert.equal(r.answer,manifest.targets['headphone-brief']);assert.equal(r.answer.split('。').length,2);assert.doesNotMatch(r.answer,/最大再生時間/);}
  for(const h of r.history)assert.notEqual(h.answer,'VIVANT、TOKYO MER、kyu、してはる');
 }
});

test('new68 questions and live27 turns remain disjoint from all fitting and prior controls',()=>{
 const seen=new Set(c.rows.map(r=>normal(r.question)));
 for(const name of ['switch-audit.json','fresh-probe.json','binding-audit.json','continuous-audit.json','prefix-audit.json','switch-rollouts.json','prefix-rollouts.json']){
  const d=read(name);for(const r of d.rows||[])seen.add(normal(r.question));for(const conv of d.conversations||[])for(const r of conv.turns)seen.add(normal(r.question));
 }
 const a=read('owner-aligned-audit.json'),live=read('owner-aligned-rollouts.json');assert.equal(a.rows.length,68);assert.equal(a.provenance.frozenBeforeFitting,true);assert.equal(a.provenance.corpusSha256,c.sourceSha256);
 for(const r of a.rows){assert.ok(!seen.has(normal(r.question)));assert.ok(t.prompt(r.question,r.history).length+t.encode(r.answer).length+1<c.provenance.context);}
 for(const r of a.rows)seen.add(normal(r.question));
 assert.equal(live.conversations.length,9);assert.equal(live.conversations.flatMap(conv=>conv.turns).length,27);
 for(const conv of live.conversations)for(const r of conv.turns){assert.ok(!seen.has(normal(r.question)));seen.add(normal(r.question));}
 for(let i=0;i<24;i++){assert.equal(a.rows[i].question,a.rows[i+24].question);assert.equal(a.rows[i].answer,a.rows[i+24].answer);assert.equal(a.rows[i].history.length,0);assert.ok(a.rows[i+24].history.length);}
});

test('complete paragraph replay retains source-page partitions, attribution and genuine sentence endings',()=>{
 const docs=new Map(c.provenance.documents.map(d=>[d.id,d])),previous=new Map(old.provenance.documents.map(d=>[d.id,d]));
 for(const d of docs.values())if(d.id.startsWith('jma:')||d.id.startsWith('maff:')||d.id.startsWith('mdn:'))assert.equal(d.textSha256,previous.get(d.id).textSha256);
 const paragraphPartitions=new Map();
 for(const [partition,key] of [['train','pretraining'],['validation','pretrainingValidation'],['test','pretrainingTest']]){
  for(const r of c[key]){
   assert.equal(docs.get(r.document).partition,partition);
   if(r.unit==='complete-paragraph'){
    const text=t.decode(r.tokens.slice(1,-1),{fatal:true});assert.ok(text.endsWith('。'));assert.equal(r.tokens[0],t.specials.bos);assert.equal(r.tokens.at(-1),t.specials.eos);assert.ok(r.tokens.length<=194);
    assert.equal(hash(text),r.paragraphSha256);assert.ok(!paragraphPartitions.has(text)||paragraphPartitions.get(text)===partition);paragraphPartitions.set(text,partition);
   }
   if(r.document.startsWith('mdn:')){assert.equal(r.license,'CC BY-SA 4.0');assert.equal(r.sourceUrl,docs.get(r.document).url);}
  }
 }
 const raw=read('owner-aligned-raw-probes.json');assert.equal(raw.rows.length,6);assert.equal(raw.provenance.frozenBeforeFitting,true);
 for(const r of raw.rows){assert.equal(docs.get(r.document).partition,'test');assert.equal(r.prefix,r.reference.slice(0,28));assert.equal(hash(r.reference),r.textSha256);}
});
