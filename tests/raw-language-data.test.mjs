import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {createTokenizer} from '../training/dialogue/tokenizer.mjs';
const root=new URL('../training/language/',import.meta.url),read=name=>JSON.parse(fs.readFileSync(new URL(name,root))),hash=b=>createHash('sha256').update(b).digest('hex');
const documents=fs.readFileSync(new URL('documents.jsonl',root),'utf8').trim().split('\n').map(s=>JSON.parse(s)),byId=new Map(documents.map(d=>[d.id,d])),split=read('split.json');
const assignments=new Map(split.assignments.map(r=>[r.document,r]));

test('expanded original prose keeps verified source conditions and attribution without Wikipedia',()=>{
 const sources=read('sources.json');assert.equal(documents.length,443);assert.equal(sources.documentsFileSha256,hash(fs.readFileSync(new URL('documents.jsonl',root))));assert.equal(split.sourceSha256,sources.documentsFileSha256);
 assert.equal(documents.reduce((n,d)=>n+d.text.length,0),sources.characters);assert.ok(sources.characters>2900000);assert.equal(new Set(documents.map(d=>d.textSha256)).size,documents.length);
 for(const d of documents){assert.equal(d.textSha256,hash(d.text));assert.ok(d.url.startsWith('https://'));assert.ok(d.license&&d.licenseUrl&&d.policyUrl&&d.modifications);assert.ok(!/wikipedia/i.test(d.url));
  if(d.site==='aozora'){assert.equal(d.workCopyright,'なし');assert.equal(d.personCopyright,'なし');assert.equal(d.orthography,'新字新仮名');assert.equal(d.bibliography['役割フラグ'],'著者');assert.ok(d.bibliography['入力者']);assert.ok(Object.hasOwn(d.bibliography,'校正者'));assert.ok(d.cardUrl);}
  else if(d.site==='mdn'){assert.match(d.license,/CC BY-SA/);assert.equal(d.author,'MDN contributors');}
  else assert.ok(['気象庁','農林水産省'].includes(d.author));
 }
});

test('entire linked documents stay in one partition and only TRAIN paragraphs fit BPE',()=>{
 assert.equal(assignments.size,documents.length);const groups=new Map();
 for(const a of assignments.values()){assert.equal(a.textSha256,byId.get(a.document).textSha256);if(groups.has(a.group))assert.equal(groups.get(a.group),a.partition);groups.set(a.group,a.partition);}
 for(const pair of split.overlapLinks)assert.equal(assignments.get(pair.left).partition,assignments.get(pair.right).partition);
 const sample=read('tokenizer-fit-sample.json');assert.equal(sample.partition,'train');const texts=[];
 for(const r of sample.rows){assert.equal(assignments.get(r.document).partition,'train');const p=byId.get(r.document).text.split('\n')[r.line];assert.equal(hash(p),r.sha256);assert.equal(p.length,r.characters);texts.push(p);}
 assert.equal(hash(texts.join('\n')),sample.textSha256);assert.equal(texts.reduce((n,s)=>n+s.length,0),sample.characters);
});

test('both BPE sizes are learned rule prefixes and every source byte and boundary target is counted once',()=>{
 const small=read('bpe-2048/tokenizer.json'),big=read('bpe-4096/tokenizer.json');assert.deepEqual(small.merges,big.merges.slice(0,2048));assert.deepEqual(small.bytes,big.bytes.slice(0,2310));
 for(const mergeCount of [2048,4096]){
  const dir='bpe-'+mergeCount+'/',tok=read(dir+'tokenizer.json'),data=read(dir+'data.json'),pieces=tok.bytes.map(s=>Buffer.from(s,'hex'));
  assert.equal(data.tokenizerSha256,hash(fs.readFileSync(new URL(dir+'tokenizer.json',root))));assert.equal(data.splitSha256,hash(fs.readFileSync(new URL('split.json',root))));
  for(const partition of ['train','validation','test']){
   const info=read(dir+partition+'.index.json'),buffer=fs.readFileSync(new URL(dir+partition+'.tokens.bin',root)),tokens=new Uint32Array(buffer.buffer,buffer.byteOffset,buffer.length/4);assert.equal(hash(buffer),info.tokensSha256);
   const rows=new Map();for(const row of info.rows){if(!rows.has(row.document))rows.set(row.document,[]);rows.get(row.document).push(row);}
   let targets=0,bytes=0;
   for(const d of info.documents){assert.equal(assignments.get(d.id).partition,partition);const full=Array.from(tokens.subarray(d.offset,d.offset+d.length));assert.equal(full[0],tok.specials.bos);assert.equal(full.at(-1),tok.specials.eos);
    const covered=rows.get(d.id).flatMap(r=>Array.from(tokens.subarray(r.offset+r.prefixLength,r.offset+r.length)));assert.deepEqual(covered,full.slice(1));assert.ok(covered.slice(0,-1).every(id=>id>=6));
    const body=Buffer.concat(covered.slice(0,-1).map(t=>pieces[t]));assert.equal(hash(body),byId.get(d.id).textSha256);assert.equal(body.toString('utf8'),byId.get(d.id).text);targets+=covered.length;bytes+=body.length;
   }
   assert.equal(targets,data.stats[partition].targetTokens);assert.equal(bytes,data.stats[partition].utf8Bytes);
  }
 }
});

test('unseen raw openings are frozen separately from tokenizer fitting, with grammar and repetition gates',()=>{
 const policy=read('generation-policy.json');assert.equal(policy.frozenBeforeTokenization,true);assert.equal(policy.probes.test.length,22);assert.equal(policy.probes.validation.length,9);
 assert.match(policy.generation.decoding,/unrestricted full vocabulary/);assert.equal(policy.generation.teacherOrOutsideModel,false);
 const train=documents.filter(d=>assignments.get(d.id).partition==='train');
 for(const partition of ['validation','test']){const seen=new Set();for(const probe of policy.probes[partition]){assert.equal(assignments.get(probe.document).partition,partition);assert.ok(!seen.has(probe.document));seen.add(probe.document);assert.ok(byId.get(probe.document).text.includes(probe.referenceParagraph));assert.ok(probe.referenceParagraph.startsWith(probe.prefix));assert.ok(!train.some(d=>d.text.includes(probe.prefix)));}}
 assert.equal(policy.acceptance.minimumGrammarScore,2);assert.equal(policy.acceptance.minimumConnectionScore,2);assert.equal(policy.acceptance.minimumSentenceSuccessRate,.8);assert.equal(policy.acceptance.minimumFullOutputNonLoopRate,.9);
 // Own adjacent heap preserves exact encoding for unseen mixed Latin/Japanese source paragraphs.
 const tok=read('bpe-4096/tokenizer.json'),loop=createTokenizer(tok),heap=createTokenizer(tok,{algorithm:'adjacent-heap'});
 for(const r of [...policy.probes.test,...policy.probes.validation])assert.deepEqual(heap.encode(r.referenceParagraph),loop.encode(r.referenceParagraph));
});
