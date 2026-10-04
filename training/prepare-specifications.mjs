import fs from 'node:fs';
import crypto from 'node:crypto';
import {tokenize} from './train-generation.mjs';
const corpus=JSON.parse(fs.readFileSync(process.argv[2]||'/tmp/4k29-spec-grammar.json'));
const source=fs.readFileSync(new URL('product-specifications.json',import.meta.url));
const memory=JSON.parse(source),vocabulary=corpus.vocabulary,ids=new Map(vocabulary.map((t,i)=>[t,i]));
const tokenId=t=>{if(!ids.has(t)){ids.set(t,vocabulary.length);vocabulary.push(t);}return ids.get(t);};
memory.sourceSha256=crypto.createHash('sha256').update(source).digest('hex');
const targets=[];
for(const product of memory.products)for(const field of product.fields)targets.push({id:product.id+':'+field.key,field,kind:'product',values:{ja:field.ja.value,en:field.en.value}});
for(const description of memory.descriptions)targets.push({id:description.id,field:description,kind:'favorite',values:{ja:description.ja,en:description.en}});
for(const target of targets){
 target.field.control=tokenId('<specification:'+target.id+'>');target.field.tokens={};
 for(const language of ['ja','en']){
  const tokens=tokenize(target.values[language],language).map(tokenId);target.field.tokens[language]=tokens;
  for(const style of ['friendly','polite']){
   const prefix=[0,corpus.controls.language[language],corpus.controls.kind[target.kind],corpus.controls.style[style],target.field.control];
   corpus.rows.push({id:'specification:'+target.id+':'+language+':'+style,language,kind:target.kind,style,weight:12,trainOnly:true,prefixLength:5,tokens:[...prefix,...tokens,1],group:'literal:'+target.id+':'+language});
  }
 }
}
corpus.specificationMemory=memory;
delete corpus.sourceSha256;corpus.sourceSha256=crypto.createHash('sha256').update(JSON.stringify(corpus)).digest('hex');
const target=process.argv[3]||'/tmp/4k29-spec-corpus.json';fs.writeFileSync(target,JSON.stringify(corpus));
console.log(JSON.stringify({target,rows:corpus.rows.length,literalRows:targets.length*4,vocabulary:vocabulary.length,maxSequence:Math.max(...corpus.rows.map(r=>r.tokens.length)),sourceSha256:corpus.sourceSha256}));
