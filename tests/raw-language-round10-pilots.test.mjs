import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const root=path.resolve('training/language/round10'),read=p=>JSON.parse(fs.readFileSync(p)),hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
test('completed pilot optimizer audit counts independent branches and selected own lineage',()=>{
 const a=read(path.join(root,'pilot-optimizer-audit.json')),choice=read(path.join(root,'vocabulary-choice.json'));assert.equal(a.actualCompletedPilotUpdates,2000);assert.equal(a.mainRunExcluded,true);assert.equal(a.mainComplete,false);assert.equal(a.selectedWeightLineageUpdates,29000);assert.equal(a.round3OnwardConfirmedCompletedUpdates,46000);assert.equal(a.round3OnwardPhysicalUpdatesLowerBound,46100);
 assert.equal(a.fullPrecisionWeightsAndOptimizer,true);assert.equal(a.pythonAndTorchRngSaved,true);assert.equal(a.vocabularyChoiceSha256,hash(path.join(root,'vocabulary-choice.json')));assert.equal(choice.generationUsed,false);assert.equal(choice.testUsed,false);
 for(const run of a.runs){const d=path.join(root,run.run),r=read(path.join(d,'result.json')),m=read(path.join(d,'metrics.json'));assert.deepEqual(run.optimizerCounters,[1000]);assert.equal(r.completedSteps,1000);assert.equal(r.bestStep,1000);assert.equal(r.parentSelectedWeightLineageUpdates,28000);assert.equal(r.ownParentOnly,true);assert.equal(r.ownRandomInitializedLineage,true);assert.equal(run.checkpointSha256,hash(path.join(d,'checkpoint.pt')));assert.equal(run.initialCheckpointSha256,hash(path.join(d,'checkpoint-0.pt')));assert.equal(run.exportModelSha256,hash(path.join(d,'model.js')));assert.equal(m.bestValidationNllPerByte,run.bestValidationNllPerByte);}
 const winner=[...choice.candidates].sort((a,b)=>a.bestValidationNllPerByte-b.bestValidationNllPerByte||a.wordMerges-b.wordMerges)[0];assert.equal(choice.selectedRun,winner.run);assert.equal(choice.wordMerges,512);assert.equal(choice.checkpointSha256,winner.checkpointSha256);
});
test('completed pilot manifest excludes main run and binds every trained artifact',()=>{
 const m=read(path.join(root,'pilot-manifest.json'));assert.equal(m.completedPilotUpdates,2000);assert.equal(m.activeMainExcluded,true);assert.equal(m.sourceManifestSha256,hash(path.join(root,'source-manifest.json')));assert.equal(m.generationUsed,false);assert.equal(m.testUsed,false);
 for(const f of m.files){assert.ok(!f.path.includes('continue-10000'));assert.equal(hash(path.join(root,f.path)),f.sha256,f.path);assert.equal(fs.statSync(path.join(root,f.path)).size,f.bytes);}
 for(const f of read(path.join(root,'source-manifest.json')).files)assert.equal(hash(path.join(root,f.path)),f.sha256,f.path);
});
