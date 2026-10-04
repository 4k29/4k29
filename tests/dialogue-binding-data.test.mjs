import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {createTokenizer} from '../training/dialogue/tokenizer.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL('../training/dialogue/'+name,import.meta.url)));
const corpus=read('binding-corpus.json'),audit=read('binding-audit.json'),tokenizer=createTokenizer(corpus.tokenizer);
test('binding targets and question families remain separated across all partitions',()=>{
 const groups=new Map(),prefixes=new Map();
 for(const row of corpus.rows){
  const prefix=tokenizer.prompt(row.question,row.history),key=JSON.stringify(prefix);
  assert.ok(!groups.has(row.group)||groups.get(row.group)===row.partition);groups.set(row.group,row.partition);
  assert.ok(!prefixes.has(key)||prefixes.get(key)===row.partition);prefixes.set(key,row.partition);
  assert.deepEqual(prefix,row.tokens.slice(0,row.prefixLength));
  assert.equal(tokenizer.decode(row.tokens.slice(row.prefixLength,-1),{fatal:true}),row.answer);
  assert.ok(row.tokens.length<=127);assert.ok(Number.isFinite(row.weight)&&row.weight>0);
  assert.equal(typeof row.semantic.subject,'string');assert.equal(typeof row.semantic.attribute,'string');
 }
 for(const row of audit.rows)assert.ok(!prefixes.has(JSON.stringify(tokenizer.prompt(row.question,row.history))));
 assert.equal(audit.provenance.bindingCorpusSha256,corpus.sourceSha256);
 const raw=fs.readFileSync(new URL('../training/dialogue/binding-corpus.json',import.meta.url),'utf8').trim().replace(/,"sourceSha256":"[0-9a-f]{64}"\}$/, '}');
 assert.equal(createHash('sha256').update(raw).digest('hex'),corpus.sourceSha256);
});
test('semantic annotations distinguish device, field and battery conditions',()=>{
 const find=intent=>corpus.rows.find(r=>r.intent===intent&&r.partition==='train');
 for(const [intent,subject,attribute] of [['earphones-cmf-anc','earphones-cmf','anc'],['earphones-cmf-battery-off','earphones-cmf','battery-off'],['earphones-cmf-battery-capacity','earphones-cmf','battery-capacity'],['headphones-battery-aac-on','headphones','battery-aac-on'],['headphones-battery-ldac-off','headphones','battery-ldac-off']]){
  assert.deepEqual(find(intent).semantic,{subject,attribute});
 }
 const missing=corpus.rows.filter(r=>r.intent==='unknown-field');assert.ok(missing.some(r=>/beats fit pro/.test(r.question)&&/重量/.test(r.question)));
 assert.ok(missing.some(r=>/cmf buds/.test(r.question)&&/ストレージ/.test(r.question)));
 assert.ok(missing.every(r=>r.answer==='その情報は分かりません。'));
});
test('new government definitions preserve attributable train-only source evidence',()=>{
 const documents=fs.readFileSync(new URL('../training/dialogue/web-language-documents.jsonl',import.meta.url),'utf8').trim().split('\n').map(JSON.parse);
 for(const fact of corpus.provenance.bindingEvidence){
  assert.ok(documents.some(d=>d.partition==='train'&&d.url===fact.url&&d.blocks.some(b=>b.text===fact.evidence)));
  assert.ok(corpus.rows.some(r=>r.intent===fact.intent&&r.partition==='train'&&r.answer===fact.answer));
 }
 assert.deepEqual(corpus.tokenizer,read('web-curriculum-corpus.json').tokenizer);
});
test('prepared MDN prose has separate attributable license and is not mixed into this run',()=>{
 const manifest=read('mdn-language-sources.json');
 const documents=fs.readFileSync(new URL('../training/dialogue/mdn-language-documents.jsonl',import.meta.url),'utf8').trim().split('\n').map(JSON.parse);
 assert.equal(documents.length,30);assert.equal(manifest.characters,documents.reduce((n,d)=>n+d.text.length,0));
 assert.ok(manifest.excludedSources.includes('Wikipedia'));assert.equal(manifest.license,'CC BY-SA 4.0');
 assert.equal(new Set(documents.map(d=>d.url)).size,documents.length);
 for(const d of documents){
  assert.equal(new URL(d.url).hostname,'developer.mozilla.org');
  const source=manifest.sources.find(s=>s.id===d.id);assert.ok(source);assert.equal(source.textSha256,d.textSha256);
  assert.equal(createHash('sha256').update(d.text).digest('hex'),d.textSha256);
  assert.ok(source.attribution.includes(d.url));assert.ok(source.modifications);
 }
 for(const key of ['pretraining','pretrainingValidation','pretrainingTest'])assert.ok(corpus[key].every(r=>!r.document.startsWith('mdn:')));
});
