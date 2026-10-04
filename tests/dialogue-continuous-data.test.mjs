import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {createTokenizer} from '../training/dialogue/tokenizer.mjs';
const file=name=>new URL('../training/dialogue/'+name,import.meta.url);
const read=name=>JSON.parse(fs.readFileSync(file(name)));
const corpus=read('continuous-corpus.json'),audit=read('continuous-audit.json');
const tokenizer=createTokenizer(corpus.tokenizer);
const hash=text=>createHash('sha256').update(text).digest('hex');

test('continuous questions, histories and arithmetic groups have separate partitions',()=>{
 const groups=new Map(),inputs=new Map();
 for(const row of corpus.rows){
  const prefix=tokenizer.prompt(row.question,row.history),key=JSON.stringify(prefix);
  assert.ok(!groups.has(row.group)||groups.get(row.group)===row.partition);groups.set(row.group,row.partition);
  assert.ok(!inputs.has(key));inputs.set(key,row.partition);
  assert.deepEqual(prefix,row.tokens.slice(0,row.prefixLength));
  assert.equal(tokenizer.decode(row.tokens.slice(row.prefixLength,-1),{fatal:true}),row.answer);
  assert.ok(row.tokens.length<=255);assert.ok(Number.isFinite(row.weight)&&row.weight>0);
 }
 for(const row of audit.rows)assert.ok(!inputs.has(JSON.stringify(tokenizer.prompt(row.question,row.history))));
 assert.equal(audit.provenance.corpusSha256,corpus.sourceSha256);
 const raw=fs.readFileSync(file('continuous-corpus.json'),'utf8').trim().replace(/,"sourceSha256":"[0-9a-f]{64}"\}$/, '}');
 assert.equal(hash(raw),corpus.sourceSha256);
 for(const {a,b,partition} of corpus.provenance.arithmeticPairs){
  const rows=corpus.rows.filter(r=>r.group===`continuous:addition:${a}:${b}`);
  assert.equal(rows.length,4);assert.ok(rows.every(r=>r.partition===partition));
  assert.ok(rows.every(r=>r.answer===`${a}+${b}=${a+b}なので、合わせて${a+b}個です。`));
 }
});

test('document streams predict each target once and end only at genuine document boundaries',()=>{
 const partitions={train:corpus.pretraining,validation:corpus.pretrainingValidation,test:corpus.pretrainingTest};
 const documents=new Map(corpus.provenance.documents.map(d=>[d.id,d]));
 for(const [partition,frames] of Object.entries(partitions)){
  const byDocument=Map.groupBy(frames,r=>r.document);
  for(const [id,rows] of byDocument){
   const document=documents.get(id);assert.ok(document);assert.equal(document.partition,partition);
   assert.equal(rows.length,document.frames);
   const tokens=[tokenizer.specials.bos];let previousEnd=1,mass=0;
   for(const [index,row] of rows.entries()){
    assert.equal(row.tokens.length,row.end-row.start);assert.ok(row.tokens.length<=193);
    assert.equal(row.start+row.prefixLength,previousEnd);
    if(index===0){assert.equal(row.prefixLength,1);assert.equal(row.tokens[0],tokenizer.specials.bos);}
    else {assert.equal(row.prefixLength,16);assert.deepEqual(row.tokens.slice(0,16),tokens.slice(-16));}
    const targets=row.tokens.slice(row.prefixLength);
    assert.equal(targets.includes(tokenizer.specials.eos),index===rows.length-1);
    assert.ok(!targets.includes(tokenizer.specials.bos));
    tokens.push(...targets);previousEnd=row.end;mass+=row.weight;
   }
   assert.ok(Math.abs(mass-1)<1e-10);assert.equal(tokens.length-1,document.tokens);
   assert.equal(tokens.at(-1),tokenizer.specials.eos);
   assert.equal(hash(tokenizer.decode(tokens.slice(1,-1),{fatal:true})),document.textSha256);
  }
 }
 assert.equal(documents.size,81);
 assert.equal(corpus.provenance.documents.filter(d=>d.id.startsWith('mdn:')&&d.partition==='train').length,24);
 assert.ok(corpus.provenance.excludedSources.includes('Wikipedia'));
});

test('MDN definitions cite training pages and retain license and source evidence',()=>{
 const documents=fs.readFileSync(file('mdn-language-documents.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
 assert.equal(corpus.provenance.mdnDefinitions.length,16);
 for(const definition of corpus.provenance.mdnDefinitions){
  const document=documents.find(d=>d.id===definition.sourceDocument);
  assert.equal(document.partition,'train');assert.equal(document.url,definition.url);
  assert.ok(definition.evidence.length>0);
  for(const paragraph of definition.evidence)assert.ok(document.blocks.some(b=>b.text===paragraph));
  assert.equal(definition.license,'CC BY-SA 4.0');
  for(const row of corpus.rows.filter(r=>r.intent===definition.intent)){
   assert.equal(row.sourceUrl,document.url);assert.equal(row.license,'CC BY-SA 4.0');assert.equal(row.answer,definition.answer);
  }
 }
 for(const key of ['pretraining','pretrainingValidation','pretrainingTest'])for(const row of corpus[key].filter(r=>r.document.startsWith('mdn:'))){
  assert.equal(row.license,'CC BY-SA 4.0');assert.equal(new URL(row.sourceUrl).hostname,'developer.mozilla.org');
 }
});

test('arithmetic audit records reversed training pairs without claiming unseen arithmetic',()=>{
 const scope=read('continuous-arithmetic-audit-scope.json');
 const pairs=new Map(corpus.provenance.arithmeticPairs.map(r=>[`${r.a}:${r.b}`,r.partition]));
 assert.equal(scope.rows.length,13);
 for(const row of scope.rows){
  assert.equal(row.partition,pairs.get(`${row.a}:${row.b}`));
  assert.equal(row.reversePartition,pairs.get(`${row.b}:${row.a}`));
  assert.equal(row.bothOrdersTest,row.partition==='test'&&row.reversePartition==='test');
  assert.ok(audit.rows.some(r=>r.id===row.id));
 }
 // This particular frozen sample contains no pair whose two orders are test-only.
 assert.equal(scope.rows.filter(r=>r.bothOrdersTest).length,0);
});

test('continuous QA keeps the requested direct wording and content boundaries',()=>{
 const targets=[...new Set(corpus.rows.map(r=>r.answer))];
 for(const phrase of ['だよ','と述べています','イヤホンについては','ヘッドホンとして','好きなドラマはTOKYO MER'])assert.ok(targets.every(text=>!text.includes(phrase)));
 const find=intent=>corpus.rows.find(r=>r.intent===intent&&r.partition==='train').answer;
 assert.equal(find('favorites'),'VIVANT、TOKYO MER、kyu、してはる');
 assert.equal(find('hobbies'),'趣味は写真・映像制作とランニングです。');
 assert.equal(find('mer'),'TOKYO MERは、鈴木亮平さん主演のTBSの日曜劇場ドラマです。');
 assert.equal(find('vivant'),'VIVANTは、堺雅人さん主演のTBSの日曜劇場ドラマです。');
 assert.equal(find('audio'),'イヤホンはBeats Fit ProとCMF Buds、ヘッドホンはNothing Headphone (1)を使っています。');
 assert.ok(find('headphone-spec').includes('40mmダイナミックドライバーを搭載し、Bluetooth 5.3とIP52'));
 const policy=read('continuous-review-policy.json');
 assert.equal(Object.keys(policy.dimensions).length,4);assert.ok(policy.passingRule.includes('All four dimensions must be 2'));
});
