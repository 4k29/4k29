import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {createTokenizer} from '../training/dialogue/tokenizer.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL('../training/dialogue/'+name,import.meta.url)));
const c=read('switch-corpus.json'),a=read('switch-audit.json'),t=createTokenizer(c.tokenizer);
const sha=value=>createHash('sha256').update(JSON.stringify(value)).digest('hex');

test('switch fresh120 inputs remain outside all source partitions and old audits',()=>{
 assert.equal(a.rows.length,120);assert.equal(a.provenance.frozenBeforeTraining,true);assert.equal(a.provenance.corpusSha256,c.sourceSha256);
 const seen=new Set(c.rows.map(r=>JSON.stringify(t.prompt(r.question,r.history))));
 for(const name of ['fresh-probe.json','binding-audit.json','continuous-audit.json','prefix-audit.json'])for(const r of read(name).rows)seen.add(JSON.stringify(t.prompt(r.question,r.history)));
 for(const r of a.rows){assert.ok(!seen.has(JSON.stringify(t.prompt(r.question,r.history))));assert.ok(t.prompt(r.question,r.history).length+t.encode(r.answer).length+1<256);}
 // Preserve Python's serialized numeric spelling when checking its source SHA.
 const raw=fs.readFileSync(new URL('../training/dialogue/switch-corpus.json',import.meta.url),'utf8').trim().replace(/,"sourceSha256":"[0-9a-f]{64}"\}$/, '}');
 assert.equal(createHash('sha256').update(raw).digest('hex'),c.sourceSha256);
});

test('switch family partitions and all27k authored encodings stay independent',()=>{
 const inputs=new Set(),groups=new Map();
 for(const r of c.rows){
  const prefix=t.prompt(r.question,r.history),key=JSON.stringify(prefix);assert.ok(!inputs.has(key));inputs.add(key);
  assert.ok(!groups.has(r.group)||groups.get(r.group)===r.partition);groups.set(r.group,r.partition);
  assert.deepEqual(prefix,r.tokens.slice(0,r.prefixLength));assert.equal(t.decode(r.tokens.slice(r.prefixLength,-1),{fatal:true}),r.answer);
  assert.ok(r.tokens.length<256);assert.ok(r.weight>0&&Number.isFinite(r.weight));
 }
 assert.equal(c.tokenizer.bytes.length,1286);assert.ok(!c.tokenizer.numericBoundaries);
 assert.ok(c.rows.filter(r=>r.partition==='train'&&r.history.length).length>12000);
});

test('same explicit questions learn to retain their own fact after different topics',()=>{
 for(const intent of ['name','role','hobbies','favorites','mer','vivant','headphone-spec','mdn-array']){
  const rows=c.rows.filter(r=>r.partition==='train'&&r.intent===intent&&r.group.startsWith('switch:form:'));
  const grouped=Map.groupBy(rows,r=>r.question);assert.ok([...grouped.values()].some(rs=>rs.length>=3&&new Set(rs.map(r=>r.answer)).size===1&&rs.some(r=>r.history.length===0)&&rs.some(r=>r.history.length>0)));
 }
 const selection=read('switch-validation-selection.json'),validation=new Set(c.rows.filter(r=>r.partition==='validation').map(r=>r.id));
 assert.equal(selection.ids.length,512);assert.equal(new Set(selection.ids).size,512);assert.ok(selection.ids.every(id=>validation.has(id)));assert.equal(sha(selection.ids),selection.idsSha256);
 const pairs=new Map(c.provenance.arithmeticPairs.map(p=>[`${p.a}:${p.b}`,p.partition]));
 for(const {a:left,b:right,bothOrdersTest} of a.provenance.arithmetic){assert.equal(pairs.get(`${left}:${right}`),'test');assert.equal(pairs.get(`${right}:${left}`),'test');assert.equal(bothOrdersTest,true);}
});

test('switch complete article streams preserve81 text hashes, splits and source rights',()=>{
 const old=new Map(read('prefix-corrected-corpus.json').provenance.documents.map(d=>[d.id,d]));
 for(const [part,key] of [['train','pretraining'],['validation','pretrainingValidation'],['test','pretrainingTest']])for(const [id,frames] of Map.groupBy(c[key],r=>r.document)){
  const source=old.get(id),targets=frames.flatMap(r=>r.tokens.slice(r.prefixLength));assert.equal(source.partition,part);assert.equal(targets.at(-1),t.specials.eos);assert.equal(targets.filter(id=>id===t.specials.eos).length,1);
  assert.ok(frames.every(r=>r.tokens.length<=129));assert.ok(Math.abs(frames.reduce((n,r)=>n+r.weight,0)-1)<1e-10);
  assert.equal(createHash('sha256').update(t.decode(targets.slice(0,-1),{fatal:true})).digest('hex'),source.textSha256);
  if(id.startsWith('mdn:'))for(const r of frames){assert.equal(r.license,'CC BY-SA 4.0');assert.equal(r.sourceUrl,source.url);}
 }
 assert.equal(c.provenance.documents.length,81);
 for(const r of c.rows)for(const bad of ['と述べています','イヤホンについては','ヘッドホンとして','だよ'])assert.ok(!r.answer.includes(bad));
 assert.deepEqual(read('switch-rollouts.json').provenance.frozenBeforeTraining,true);
});
