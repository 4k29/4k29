import fs from 'node:fs';
import crypto from 'node:crypto';
import {generationModel as base} from '../docs/generation-model.js';
import {directVoicePath} from '../docs/response-voice.js';
import {favoriteGrammar} from '../docs/favorite-grammar.js';
import {knowledgeGrammar} from '../docs/knowledge-grammar.js';
const vocabulary=[...base.vocabulary],controls={language:{},kind:{},style:{}};
for(const [key,values] of Object.entries({language:['ja','en'],kind:[...new Set(base.paths.map(p=>p.kind))].sort(),style:['polite','friendly']}))for(const value of values){controls[key][value]=vocabulary.length;vocabulary.push('<'+key+':'+value+'>');}
const pad=vocabulary.length;vocabulary.push('<pad>');
const paths=[...(process.argv.includes('--direct-only')?base.paths.filter(p=>directVoicePath(p,base.vocabulary)):base.paths)];
if(process.argv.includes('--extended'))for(const language of ['ja','en']){
 paths.push(...favoriteGrammar(language,base.vocabulary).map(p=>({...p,kind:'favorite'})));
 paths.push(...knowledgeGrammar(language,base.vocabulary).map(p=>({...p,kind:'writing'})));
}
const rows=paths.map(p=>({id:p.id,language:p.language,kind:p.kind,style:p.style,weight:p.quality===1?2:1,tokens:[0,controls.language[p.language],controls.kind[p.kind],controls.style[p.style],...p.tokens,1],group:p.language+':'+p.kind+':'+p.tokens.join(',')}));
const source={schemaVersion:1,baseVersion:base.version,baseSourceSha256:base.training.sourceSha256,vocabulary,controls,pad,rows};
const sourceSha256=crypto.createHash('sha256').update(JSON.stringify(source)).digest('hex');
const corpus={...source,sourceSha256},target=process.argv.slice(2).find(arg=>!arg.startsWith('--'))||'/tmp/4k29-transformer-corpus.json';
fs.writeFileSync(target,JSON.stringify(corpus));
console.log(JSON.stringify({target,sourceSha256,rows:rows.length,vocabulary:vocabulary.length,maxSequence:Math.max(...rows.map(r=>r.tokens.length))}));
