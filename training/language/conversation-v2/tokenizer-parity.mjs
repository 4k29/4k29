// Text encoder parity only: no model, answers, training, or learned asset edits.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {createTokenizer} from '../../dialogue/tokenizer.mjs';
const args=Object.fromEntries(Array.from({length:(process.argv.length-2)/2},(_,i)=>[process.argv[2+i*2],process.argv[3+i*2]]));
for(const key of ['--tokenizer','--inputs','--output'])if(!args[key])throw Error('Missing '+key);
if(fs.existsSync(args['--output']))throw Error('Refuse output overwrite');
const tokenizerBytes=fs.readFileSync(args['--tokenizer']);
const config=JSON.parse(tokenizerBytes.toString('utf8'));
// Replace the six special NAMES for the legacy API, not their IDs or count.
// encode() does not call prompt(), normalize text, or insert any role token.
const alias={pad:0,bos:1,eos:2,user:3,assistant:4,turn:5};
if(Object.keys(config.specials).length!==6||Object.values(config.specials).some((v,i)=>v!==i))throw Error('Unexpected specials');
const encoder=createTokenizer({...config,specials:alias},{algorithm:'adjacent-heap'});
const payload=JSON.parse(fs.readFileSync(args['--inputs'],'utf8'));
const rows=[];
for(const sample of payload.rows){
 const actual=encoder.encode(sample.text);
 const utf8=Buffer.from(new TextEncoder().encode(sample.text)).toString('hex');
 const decoded=encoder.decode(actual,{fatal:true});
 const reconstructed=Buffer.from(decoded,'utf8').toString('hex');
 const exact=actual.length===sample.expectedTokens.length&&actual.every((x,i)=>x===sample.expectedTokens[i]);
 rows.push({id:sample.id,source:sample.source,actualTokens:actual,utf8Hex:utf8,reconstructedUtf8Hex:reconstructed,
   tokenIdsExact:exact,roundtripExact:decoded===sample.text&&reconstructed===sample.utf8Hex,sourceUtf8Exact:utf8===sample.utf8Hex});
}
const result={status:rows.every(r=>r.tokenIdsExact&&r.roundtripExact&&r.sourceUtf8Exact)?'PASS':'FAIL',
 nodeVersion:process.version,algorithm:'Existing own tokenizer.mjs createTokenizer.encode adjacent-heap',
 tokenizerSha256:crypto.createHash('sha256').update(tokenizerBytes).digest('hex'),
 specialsNameAliasOnly:alias,byteOffset:6,noPromptNormalizationCalled:true,
 modelObjectsConstructed:0,optimizerUpdates:0,generatedAnswers:0,rows};
fs.writeFileSync(args['--output'],JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({status:result.status,cases:rows.length,tokenMismatches:rows.filter(r=>!r.tokenIdsExact).length,
 roundtripFailures:rows.filter(r=>!r.roundtripExact||!r.sourceUtf8Exact).length,nodeVersion:process.version}));
if(result.status!=='PASS')process.exitCode=1;
