// Own byte-level BPE, matching tokenizer.py exactly; no model/tokenizer imports.
import {createAdjacentBPE} from './bpe_heap.mjs';
export function createTokenizer(config,{algorithm='rank-loop'}={}){
 if(!['rank-loop','adjacent-heap'].includes(algorithm))throw RangeError('Unknown own BPE algorithm');
 const specials=config.specials,offset=Object.keys(specials).length;
 const pieces=config.bytes.map(hex=>Uint8Array.from(hex.match(/../g)||[],p=>parseInt(p,16)));
 function encodeLoop(text){
  let tokens=[...new TextEncoder().encode(text)].map(byte=>byte+offset);
  for(const [left,right,token] of config.merges){const next=[];for(let i=0;i<tokens.length;i++){if(tokens[i]===left&&tokens[i+1]===right){next.push(token);i++;}else next.push(tokens[i]);}tokens=next;}
  return tokens;
 }
 const encode=algorithm==='adjacent-heap'?createAdjacentBPE(config):encodeLoop;
 function decode(tokens,{fatal=false}={}){
  const length=tokens.reduce((n,id)=>n+pieces[id].length,0),bytes=new Uint8Array(length);let cursor=0;
  for(const id of tokens){bytes.set(pieces[id],cursor);cursor+=pieces[id].length;}
  return new TextDecoder('utf-8',{fatal}).decode(bytes);
 }
 function prompt(question,history=[]){
  const tokens=[specials.bos],normalize=q=>String(q).normalize('NFKC').toLowerCase();
  for(const turn of history)tokens.push(specials.user,...encode(normalize(turn.question)),specials.assistant,...encode(turn.answer),specials.turn);
  tokens.push(specials.user,...encode(normalize(question)),specials.assistant);return tokens;
 }
 return {encode,decode,prompt,specials};
}
