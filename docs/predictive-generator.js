import {generationModel} from './generation-model.js?v=20261004-transformer-5b';
import {naturalGrammarPaths,conversationalJapanese} from './response-voice.js?v=20261004-transformer-5b';
import {favoriteGrammar} from './favorite-grammar.js?v=20261004-transformer-5b';
import {knowledgeGrammar} from './knowledge-grammar.js?v=20261004-transformer-5b';
import {predictNextTokens} from './next-token-model.js?v=20261004-transformer-5b';
import {predictNeuralNextTokens,neuralVersion,neuralArchitecture} from './neural-inference.js?v=20261004-transformer-5b';
const tries=new Map(),searches=new Map();
function grammarTrie(language,kind){
 const key=language+':'+kind;if(tries.has(key))return tries.get(key);
 const base=kind==='knowledge'?knowledgeGrammar(language,generationModel.vocabulary):kind==='favoriteThing'?favoriteGrammar(language,generationModel.vocabulary):generationModel.paths.filter(p=>p.language===language&&p.kind===kind);
 const paths=naturalGrammarPaths(base,generationModel.vocabulary),root={next:new Map(),rows:[]};
 for(const row of paths){let node=root;for(const token of [...row.tokens,1]){if(!node.next.has(token))node.next.set(token,{next:new Map(),rows:[]});node=node.next.get(token);}node.rows.push(row);}
 const grammar={root,paths};tries.set(key,grammar);return grammar;
}
function grams(text){return new Set(Array.from({length:Math.max(0,text.length-2)},(_,i)=>text.slice(i,i+3)));}
function similarity(a,b){let common=0;for(const term of a)if(b.has(term))common++;return common/(a.size+b.size-common||1);}
function render(tokens,values,context){
 let template=tokens.filter(id=>id!==1).map(id=>generationModel.vocabulary[id]).join('');
 if(context.language==='ja'&&context.style==='friendly')template=conversationalJapanese(template);
 return template.replace(/\{(value|label)\}/g,(_,key)=>values[key]||'');
}
const focuses={name:/名前|呼び|\bname\b/,role:/職業|身分|立場|\b(?:role|occupation)\b/,tool:/ツール|開発|制作|\b(?:tool|develop)\b/,workflow:/流れ|順|手順|\b(?:process|sequence|steps)\b/,responsibility:/担当|役割|自分|\b(?:handle|role|contribution)\b/,preference:/重視|大切|こだわ|\b(?:priorities|value|care)\b/,hobbies:/趣味|\bhobb/,audio:/イヤホン|ヘッドホン|\b(?:earbuds|headphones)\b/,runningApp:/アプリ|\bapp\b/,runningShoes:/靴|シューズ|\bshoes\b/,writing:/記事|テーマ|\b(?:article|topic)\b/,favorite:/推し|好きな人|\bfavou?rite\b/,subscription:/サブスク|契約|\bsubscri/};
export function generateCandidates(kind,language,values,options={}){
 const context={kind:kind==='knowledge'?'writing':kind==='favoriteThing'?'favorite':kind,language,style:options.style||'polite'},grammar=grammarTrie(language,kind);
 if(!grammar.paths.length)throw Error('Unsupported generation kind: '+kind);
 const searchKey=language+':'+kind+':'+context.style;
 let search=searches.get(searchKey);
 if(!search){
 let active=[{node:grammar.root,tokens:[],history:[0,0,0],logProbability:0}],completed=[],transitions=0;
 // The trie permits only complete, authored grammatical paths. Every step is
 // scored by predicted next-token probability; a fact span is never split.
 for(let step=0;active.length&&step<100;step++){
  const next=[];
  for(const beam of active){
   const allowed=[...beam.node.next.keys()],statistical=new Map(predictNextTokens(generationModel,context,beam.history,allowed).map(p=>[p.token,p.probability]));
   for(const prediction of predictNeuralNextTokens(context,beam.tokens,allowed)){
   const probability=.85*prediction.probability+.15*statistical.get(prediction.token);
   transitions++;const node=beam.node.next.get(prediction.token),candidate={node,tokens:[...beam.tokens,prediction.token],history:[...beam.history.slice(-2),prediction.token],logProbability:beam.logProbability+Math.log(probability)};
   if(node.rows.length)for(const row of node.rows)completed.push({tokens:candidate.tokens,logProbability:candidate.logProbability,row});else next.push(candidate);
   }
  }
  active=next.sort((a,b)=>b.logProbability/b.tokens.length-a.logProbability/a.tokens.length||b.logProbability-a.logProbability).slice(0,64);
 }
 // The trained weights, grammar and conditioning tokens are immutable. Reuse
 // their likelihoods; question focus, length and repetition are scored afresh.
 search={completed,transitions};searches.set(searchKey,search);
 }
 const {completed,transitions}=search;
 const previous=(options.previous||[]).slice(-8).map(grams);
 let paths=completed.filter(c=>c.row.style===context.style);
 if(options.length==='detail'&&paths.some(c=>c.row.detail))paths=paths.filter(c=>c.row.detail);
 if(options.length==='brief')paths=paths.filter(c=>!c.row.detail);
 if(options.length==='brief'){
  const frameLength=c=>c.tokens.reduce((n,id)=>n+(/^[{<]/.test(generationModel.vocabulary[id])?0:generationModel.vocabulary[id].length),0);
  paths=[...paths].sort((a,b)=>frameLength(a)-frameLength(b)).slice(0,Math.max(4,Math.ceil(paths.length/4)));
 }
 const lengths=paths.map(c=>c.tokens.reduce((n,id)=>n+(/^[{<]/.test(generationModel.vocabulary[id])?0:generationModel.vocabulary[id].length),0)),min=Math.min(...lengths),max=Math.max(...lengths);
 const unique=new Map();
 for(const [index,candidate] of paths.entries()){
  if(options.length==='brief'&&lengths[index]>min+(max-min)*.4)continue;
  const text=render(candidate.tokens,values,context),novelty=1-Math.max(0,...previous.map(p=>similarity(grams(text),p)));
  const features=[1,options.length==='brief'?1-(lengths[index]-min)/(max-min||1):0,options.length==='detail'?(candidate.row.detail?1:0):options.length==='brief'?(candidate.row.detail?-1:0):candidate.row.detail?-.5:0,focuses[kind]?.test(options.question||'')?(focuses[kind].test(text)?1:0):.5,Math.exp(candidate.logProbability/candidate.tokens.length),candidate.row.quality,novelty];
  const ending=text.match(/(?:だよ|です|います|いる|ある|する)。(?:\s*)$/)?.[0];
  const endingRepetition=ending?(options.previous||[]).slice(-3).filter(reply=>reply.trimEnd().endsWith(ending)).length:0;
  const score=features.reduce((n,f,i)=>n+f*generationModel.preferenceWeights[i],0)-endingRepetition*.4-(ending==='だよ。'?.15:0),result={text,score,features,pathId:candidate.row.id,tokens:candidate.tokens,meanLogProbability:candidate.logProbability/candidate.tokens.length,transitions};
  if(!unique.has(text)||score>unique.get(text).score)unique.set(text,result);
 }
 return [...unique.values()].sort((a,b)=>b.score-a.score||a.pathId.localeCompare(b.pathId));
}
export function createSentenceRenderer(options={}){
 const cache=new Map(),trace=[];
 return {trace,render(kind,language,value,label,variant=0){
  const key=JSON.stringify([kind,language,value,label]);if(!cache.has(key))cache.set(key,generateCandidates(kind,language,{value,label},options));
  const candidates=cache.get(key),pool=candidates.slice(0,options.length==='brief'?8:16),choice=pool[((variant%pool.length)+pool.length)%pool.length];
  if(!choice)throw Error('No valid grammatical candidate');
  trace.push({kind,pathId:choice.pathId,meanLogProbability:choice.meanLogProbability,score:choice.score});
  return choice.text;
 }};
}
export const generationVersion=neuralVersion;
export const generationArchitecture=neuralArchitecture;
