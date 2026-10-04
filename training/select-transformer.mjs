import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {generationModel} from '../docs/generation-model.js';
const folder=path.resolve(process.argv[2]||'/tmp/4k29-neural-candidates'),root=fileURLToPath(new URL('..',import.meta.url));
const provided=process.argv.slice(3).filter(arg=>!arg.startsWith('--'));
const minimum=Number(process.argv.find(arg=>arg.startsWith('--minimum-updates='))?.split('=')[1]??10000);
const candidates=(provided.length?provided:['steadyA','steadyB','steadyC']).map(name=>({name,...JSON.parse(fs.readFileSync(path.join(folder,name+'-training.json')))}));
for(const candidate of candidates){
 if(candidate.training.baseSourceSha256!==generationModel.training.sourceSha256)throw Error('Candidate corpus is stale: '+candidate.name);
 if(!Number.isFinite(candidate.training.finalValidationLoss))throw Error('Invalid validation result');
 if(candidate.training.completedSteps<minimum||candidate.training.bestStep<minimum)throw Error('Candidate does not meet minimum updates: '+candidate.name);
}
const selected=[...candidates].sort((a,b)=>a.training.finalValidationLoss-b.training.finalValidationLoss)[0];
const source=fs.readFileSync(path.join(folder,selected.name+'.js'));
fs.writeFileSync(path.join(root,'docs/neural-model.js'),source);
for(const suffix of ['training','reference'])fs.copyFileSync(path.join(folder,selected.name+'-'+suffix+'.json'),path.join(root,'training/transformer-'+suffix+'.json'));
const report={selected:selected.name,minimumUpdates:minimum,reason:selected.training.checkpointPolicy==='after-all-requested-updates'?'Completed every requested round and update. An earlier checkpoint does not substitute for the requested update count; external holdout was not consulted.':'Lowest token-level validation loss among checkpoints meeting the minimum update count on fixed unseen phrase groups; external holdout was not consulted.',modelSha256:crypto.createHash('sha256').update(source).digest('hex'),totalCompletedSteps:candidates.reduce((n,c)=>n+c.training.completedSteps,0),candidates};
fs.writeFileSync(path.join(root,'training/transformer-selection.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({selected:report.selected,totalCompletedSteps:report.totalCompletedSteps,validation:candidates.map(c=>({name:c.name,seed:c.training.seed,dropout:c.config.dropout,bestStep:c.training.bestStep,loss:c.training.finalValidationLoss})),modelSha256:report.modelSha256},null,2));
