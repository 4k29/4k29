import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {createTokenizer} from '../training/dialogue/tokenizer.mjs';
const file=name=>new URL('../training/dialogue/'+name,import.meta.url);
const read=name=>JSON.parse(fs.readFileSync(file(name)));
const corpus=read('prefix-corrected-corpus.json'),audit=read('prefix-corrected-audit.json'),tokenizer=createTokenizer(corpus.tokenizer);

test('prefix BPE is learned from own training text and preserves numeric runs',()=>{
 assert.equal(corpus.tokenizer.numericBoundaries,true);assert.equal(corpus.tokenizer.bytes.length,1798);
 const pieces=corpus.tokenizer.bytes.map(hex=>Buffer.from(hex,'hex'));
 for(const piece of pieces.slice(6))if([...piece].some(b=>b>=48&&b<=57))assert.ok([...piece].every(b=>b>=48&&b<=57));
 for(let n=10;n<=40;n++)assert.ok(pieces.some(p=>p.equals(Buffer.from(String(n)))));
 for(const word of ['Array','String','Set','textarea','color','font-family'])assert.ok(pieces.some(p=>p.equals(Buffer.from(word))));
 assert.notDeepEqual(corpus.tokenizer,read('continuous-corpus.json').tokenizer);
});

test('prefix questions and histories are separated and match independent JavaScript encoding',()=>{
 const inputs=new Set(),groups=new Map();
 for(const row of corpus.rows){
  const prefix=tokenizer.prompt(row.question,row.history),key=JSON.stringify(prefix);
  assert.ok(!inputs.has(key));inputs.add(key);
  assert.ok(!groups.has(row.group)||groups.get(row.group)===row.partition);groups.set(row.group,row.partition);
  assert.deepEqual(prefix,row.tokens.slice(0,row.prefixLength));
  assert.equal(tokenizer.decode(row.tokens.slice(row.prefixLength,-1),{fatal:true}),row.answer);
  assert.ok(row.tokens.length<192);assert.ok(Number.isFinite(row.weight)&&row.weight>0);
 }
 for(const row of audit.rows)assert.ok(!inputs.has(JSON.stringify(tokenizer.prompt(row.question,row.history))));
 assert.equal(audit.rows.length,100);assert.equal(audit.provenance.corpusSha256,corpus.sourceSha256);
 const raw=fs.readFileSync(file('prefix-corrected-corpus.json'),'utf8').trim().replace(/,"sourceSha256":"[0-9a-f]{64}"\}$/, '}');
 assert.equal(createHash('sha256').update(raw).digest('hex'),corpus.sourceSha256);
});

test('corrected references are explicit and all100 original audit prompts and golds stay frozen',()=>{
 assert.deepEqual(audit.rows,read('prefix-audit.json').rows);
 for(const row of corpus.rows.filter(r=>r.intent.startsWith('reference-')&&r.group.includes(':True:')))assert.ok(!/^(?:前の|前に)/.test(row.question));
 assert.ok(corpus.provenance.referenceClarification);
});

test('both orders of every new arithmetic audit pair remain outside training and validation',()=>{
 const pairs=new Map(corpus.provenance.arithmeticPairs.map(r=>[`${r.a}:${r.b}`,r.partition]));
 for(const pair of corpus.provenance.arithmeticPairs)assert.equal(pair.partition,pairs.get(`${pair.b}:${pair.a}`));
 for(const row of corpus.rows.filter(r=>r.intent==='addition')){
  const [,a,b]=row.answer.match(/^(\d+)\+(\d+)=/);assert.equal(row.partition,pairs.get(`${a}:${b}`));
 }
 assert.equal(audit.provenance.arithmetic.length,8);
 for(const {a,b,id,bothOrdersTest} of audit.provenance.arithmetic){
  assert.equal(pairs.get(`${a}:${b}`),'test');assert.equal(pairs.get(`${b}:${a}`),'test');assert.equal(bothOrdersTest,true);
  assert.ok(audit.rows.some(r=>r.id===id&&r.answer===`${a}+${b}=${a+b}なので、合わせて${a+b}個です。`));
 }
});

test('retokenized full source documents keep attributable text and page partitions',()=>{
 const old=read('continuous-corpus.json'),previous=new Map(old.provenance.documents.map(d=>[d.id,d]));
 for(const [partition,key] of [['train','pretraining'],['validation','pretrainingValidation'],['test','pretrainingTest']]){
  const documents=Map.groupBy(corpus[key],r=>r.document);
  for(const [id,frames] of documents){
   const source=previous.get(id),metadata=corpus.provenance.documents.find(d=>d.id===id);assert.equal(source.partition,partition);
   assert.equal(metadata.textSha256,source.textSha256);assert.equal(metadata.originalTextSha256,source.originalTextSha256);
   const targets=frames.flatMap(f=>f.tokens.slice(f.prefixLength));
   assert.equal(targets.filter(t=>t===tokenizer.specials.eos).length,1);assert.equal(targets.at(-1),tokenizer.specials.eos);
   assert.ok(frames.every(f=>f.tokens.length<=161));
   assert.ok(Math.abs(frames.reduce((n,r)=>n+r.weight,0)-1)<1e-10);
   const text=tokenizer.decode(targets.slice(0,-1),{fatal:true});assert.equal(createHash('sha256').update(text).digest('hex'),source.textSha256);
   if(id.startsWith('mdn:'))for(const frame of frames){assert.equal(frame.license,'CC BY-SA 4.0');assert.equal(frame.sourceUrl,source.url);}
  }
 }
 assert.equal(corpus.provenance.documents.length,81);assert.ok(corpus.provenance.excludedSources.includes('Wikipedia'));
});

test('prefix target style keeps direct replies and adapts greeting to the input',()=>{
 const find=intent=>corpus.rows.find(r=>r.intent===intent&&r.partition==='train').answer;
 assert.equal(find('favorites'),'VIVANT、TOKYO MER、kyu、してはる');assert.equal(find('hobbies'),'趣味は写真・映像制作とランニングです。');
 for(const row of corpus.rows)for(const phrase of ['と述べています','イヤホンについては','ヘッドホンとして','だよ'])assert.ok(!row.answer.includes(phrase));
 for(const row of corpus.rows.filter(r=>r.intent==='greeting'||r.intent.startsWith('greeting-'))){
  if(row.question.includes('こんばんは'))assert.ok(row.answer.startsWith('こんばんは。'));
  if(row.question.includes('おはよう'))assert.ok(row.answer.startsWith('おはよう。'));
 }
});
