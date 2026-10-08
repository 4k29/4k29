import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const root=path.resolve('training/language/round10');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
test('word training reports actual optimizer branch counts and owned selected lineage',()=>{
 const a=read(path.join(root,'optimizer-audit.json')),v=read(path.join(root,'vocabulary-choice.json'));
 assert.equal(a.actualCompletedPilotUpdates,2000);assert.equal(a.actualCompletedMainUpdates,10000);assert.equal(a.actualCompletedUpdatesThisRound,12000);assert.equal(a.round3OnwardConfirmedCompletedUpdates,56000);assert.equal(a.round3OnwardPhysicalUpdatesLowerBound,56100);
 assert.deepEqual(a.pilots.map(p=>p.optimizerCounters),[[1000],[1000]]);assert.deepEqual(a.main.optimizerCounters,[10000]);assert.equal(a.main.parentSelectedWeightLineageUpdates,28000+v.selectedPilotStep);assert.equal(a.selectedWeightLineageUpdates,a.main.parentSelectedWeightLineageUpdates+a.main.bestStep);
 assert.equal(v.generationUsed,false);assert.equal(v.testUsed,false);assert.equal(a.fullPrecisionWeightsAndOptimizer,true);assert.equal(a.pythonAndTorchRngSaved,true);
 for(const r of [...a.pilots,a.main])assert.equal(r.checkpointSha256,hash(path.join(root,r.run,'checkpoint.pt')));
 const winner=[...v.candidates].sort((a,b)=>a.bestValidationNllPerByte-b.bestValidationNllPerByte||a.wordMerges-b.wordMerges)[0];assert.equal(v.selectedRun,winner.run);assert.equal(v.checkpointSha256,winner.checkpointSha256);
});
test('unedited raw continuations retain measured numerical divergence and all language judgments',()=>{
 const c=read(path.join(root,'comparison.json')),v=read(path.join(root,'vocabulary-choice.json')),choice=read(path.join(root,'checkpoint-choice.json')),names=['main-initial-0',`word-${v.wordMerges}-continue-10000`];
 assert.equal(choice.vocabularyChoiceSha256,hash(path.join(root,'vocabulary-choice.json')));assert.equal(choice.meaningPolicySha256,hash(path.join(root,'full-meaning-policy.json')));assert.equal(c.testStillUnopened,true);assert.equal(c.publicModelReplaced,false);
 for(const name of names){
  const d=path.join(root,name),g=read(path.join(d,'validation.json')),r=read(path.join(d,'validation-review.json')),j=read(path.join(d,'validation-js.json')),m=read(path.join(d,'validation-manual.json'));
  assert.equal(g.rows.length,17);assert.equal(g.maxNewTokens,192);assert.equal(r.generationSha256,hash(path.join(d,'validation.json')));assert.equal(m.generationSha256,r.generationSha256);assert.equal(m.meaningPolicySha256,choice.meaningPolicySha256);assert.equal(r.independentHumanEvaluation,false);
  assert.equal(j.completeGenerationParity,c.runs[name].completeGreedySequenceParity);assert.equal(j.modelSha256,g.modelFileSha256);assert.ok(j.references.every(ref=>ref.maxAbsoluteError<=2e-4));
  const mismatches=[];for(let i=0;i<17;i++){let different=false;for(const key of ['id','text','tokens','eos','validUtf8','validTokens','inputTokens']){assert.deepEqual(g.rows[i][key],r.rows[i][key]);different ||= JSON.stringify(g.rows[i][key])!==JSON.stringify(j.rows[i][key]);}if(different)mismatches.push(g.rows[i].id);}
  assert.equal(j.completeGenerationParity,mismatches.length===0);assert.equal(c.runs[name].matchingRawSequences,17-mismatches.length);if(mismatches.length){const diag=read(path.join(root,'numerical-divergence.json'));assert.deepEqual(mismatches,diag.rows.map(r=>r.id));assert.ok(diag.rows.every(r=>r.referenceTolerancePassed&&r.argmaxChoicesReproduced));assert.equal(diag.noOutputRepair,true);assert.equal(diag.noWeightChange,true);}
  assert.deepEqual(Object.keys(r.scopes).sort(),['expanded17','original9','parent13']);assert.equal(r.gatePassed,Object.values(r.scopes).every(s=>s.gatePassed));
  for(const s of Object.values(r.scopes))for(const group of Object.values(s.groups))assert.equal(group.gatePassed,group.firstSentenceSuccessRate>=.8&&group.fullOutputNonLoopRate>=.9&&group.fullOutputMeaningfulRate>=.8);
  for(const row of m.rows){assert.equal(typeof row.fullOutputMeaningful,'boolean');assert.ok(row.reason);}
 }
 assert.equal(c.naturalLanguageEstablished,c.runs[names[1]].naturalLanguageEstablished);
});
test('all result files, source snapshot and parent inventories remain SHA-bound',()=>{
 const m=read(path.join(root,'reproducibility-manifest.json'));assert.equal(m.completedUpdatesThisRound,12000);
 for(const f of m.files){assert.equal(hash(path.join(root,f.path)),f.sha256,f.path);assert.equal(fs.statSync(path.join(root,f.path)).size,f.bytes);}
 for(const f of read(path.join(root,'pilot-manifest.json')).files)assert.equal(hash(path.join(root,f.path)),f.sha256);
 for(const [phase,file] of [['round8','reproducibility-manifest.json'],['round9-source','source-manifest.json']]){const p=path.resolve('training/language',phase);for(const f of read(path.join(p,file)).files)assert.equal(hash(path.join(p,f.path)),f.sha256);}
 const f=read(path.join(root,'evaluation-freeze.json'));assert.equal(f.developmentGenerationAbsentAtFreeze,true);assert.equal(f.meaningPolicySha256,hash(path.join(root,'full-meaning-policy.json')));for(const helper of f.helperSources)assert.equal(hash(path.join(root,helper.path)),helper.sha256);
 for(const [name,r] of Object.entries(read(path.join(root,'comparison.json')).runs))assert.equal(fs.existsSync(path.join(root,name,'test.json')),false);
 const plot=read(path.join(root,'learning-curves-source.json'));assert.equal(plot.completedUpdates,12000);assert.equal(plot.manualComparisonSha256,hash(path.join(root,'comparison.json')));
});
