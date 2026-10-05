import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {createHash} from 'node:crypto';
const root=new URL('../training/language/',import.meta.url),read=n=>JSON.parse(fs.readFileSync(new URL(n,root))),hash=b=>createHash('sha256').update(b).digest('hex');
const docs=new Map(fs.readFileSync(new URL('documents.jsonl',root),'utf8').trim().split('\n').map(s=>{const d=JSON.parse(s);return [d.id,d];}));
const selection=read('paragraph-bpe-4096/paragraphs.json'),split=new Map(read('split.json').assignments.map(a=>[a.document,a.partition]));

test('raw paragraph curriculum selects actual complete attributed prose without adding QA or changing held groups',()=>{
 const data=read('paragraph-bpe-4096/data.json');assert.equal(data.sourceSha256,hash(fs.readFileSync(new URL('documents.jsonl',root))));assert.equal(data.tokenizerFittedAgain,false);assert.equal(data.paragraphSelectionsSha256,hash(fs.readFileSync(new URL('paragraph-bpe-4096/paragraphs.json',root))));assert.deepEqual(read('paragraph-bpe-4096/tokenizer.json'),read('bpe-4096/tokenizer.json'));
 assert.equal(selection.filter(r=>r.partition==='train').length,13447);
 for(const r of selection){const source=docs.get(r.document);assert.equal(r.partition,split.get(r.document));assert.equal(r.sourceTextSha256,source.textSha256);const p=source.text.split('\n')[r.line].trim();assert.equal(hash(p),r.paragraphSha256);assert.ok(/[。！？」]$/.test(p));assert.ok(p.length>=40);assert.doesNotMatch(p,/参考資料|相談電話|電話番号|消費者の部屋|0\d{1,4}[-ー]\d{1,4}[-ー]\d{3,4}/);}
});

test('all stochastic TRAIN views keep every original byte, source provenance and true paragraph-end EOS',()=>{
 const tok=read('paragraph-bpe-4096/tokenizer.json'),pieces=tok.bytes.map(s=>Buffer.from(s,'hex')),data=read('paragraph-bpe-4096/data.json');
 for(const partition of ['train','validation','test']){
  const info=read('paragraph-bpe-4096/'+partition+'.index.json'),b=fs.readFileSync(new URL('paragraph-bpe-4096/'+partition+'.tokens.bin',root)),values=new Uint32Array(b.buffer,b.byteOffset,b.length/4);assert.equal(hash(b),info.tokensSha256);const rows=new Map();for(const r of info.rows){if(!rows.has(r.unit))rows.set(r.unit,[]);rows.get(r.unit).push(r);}
  let count=0;for(const d of info.documents){assert.equal(split.get(d.sourceDocument),partition);const source=docs.get(d.sourceDocument).text.split('\n')[d.line].trim();const full=Array.from(values.subarray(d.offset,d.offset+d.length));assert.equal(full[0],1);assert.equal(full.at(-1),2);assert.ok(full.slice(1,-1).every(t=>t>=6));assert.equal(Buffer.concat(full.slice(1,-1).map(t=>pieces[t])).toString('utf8'),source);assert.equal(hash(source),d.textSha256);const covered=rows.get(d.id).flatMap(r=>Array.from(values.subarray(r.offset+r.prefixLength,r.offset+r.length)));assert.deepEqual(covered,full.slice(1));count+=covered.length;
   if(partition!=='train')assert.equal(d.variant,0);
  }
  assert.equal(count,data.stats[partition].targetTokens);assert.equal(info.documents.length,data.stats[partition].views);
 }
});

test('TRAIN segmentation variants are augmentation, not new unique raw prose or held-token fitting',()=>{
 const data=read('paragraph-bpe-4096/data.json'),train=read('paragraph-bpe-4096/train.index.json');const views=new Map();
 for(const d of train.documents){const key=d.sourceDocument+':'+d.line;if(!views.has(key))views.set(key,[]);views.get(key).push(d.variant);}
 for(const probabilities of views.values())assert.deepEqual(probabilities,[0,.15,.3]);assert.equal(views.size,data.stats.train.uniqueParagraphs);assert.equal(data.stats.train.viewUtf8Bytes,3*data.stats.train.uniqueSourceUtf8Bytes);
 assert.equal(read('generation-policy.json').probes.test.length,22);assert.equal(read('generation-policy.json').acceptance.minimumSentenceSuccessRate,.8);
});
