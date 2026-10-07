import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {gunzipSync} from 'node:zlib';
const root=path.resolve('training/language/round8');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');

test('own character run binds actual updates, source identities and saved comparison',()=>{
  const d=path.join(root,'expanded-characters-10000'),r=read(path.join(d,'result.json'));
  const a=read(path.join(root,'optimizer-audit.json')),c=read(path.join(root,'checkpoint-choice.json'));
  assert.equal(r.completedRun,true);assert.equal(r.completedSteps,10000);assert.equal(r.requestedSteps,10000);
  assert.equal(a.actualAdditionalOptimizerUpdates,10000);assert.equal(a.observedDiscardedUpdates,100);assert.equal(a.physicalAdditionalUpdatesLowerBound,10100);assert.equal(a.unloggedDiscardedUpdatesUnknown,true);
  const recovery=read(path.join(root,'recovery.json'));assert.equal(a.recoveryRecordSha256,hash(path.join(root,'recovery.json')));assert.equal(recovery.resumeCheckpointSha256,hash(path.join(root,recovery.resumeCheckpointPath)));assert.equal(recovery.priorLogSha256,hash(path.join(root,recovery.priorLogPath)));
assert.deepEqual(a.optimizerStepCounters,[10000]);
  assert.equal(a.selectedWeightLineageUpdates,r.parentSelectedWeightLineageUpdates+r.bestStep);assert.equal(a.baselineAddsUpdates,false);
  assert.equal(a.fullPrecisionWeightsAndOptimizer,true);assert.equal(a.pythonAndTorchRngSaved,true);
  assert.equal(r.randomInitialization,false);assert.equal(r.ownParentOnly,true);assert.equal(r.ownRandomInitializedLineage,true);assert.equal(r.optimizerReset,true);assert.equal(r.wordMerges,0);
  for(const k of ['externalWeights','externalTokenizer','externalInferenceAPI'])assert.equal(r[k],false);
  assert.equal(r.checkpointSha256,hash(path.join(d,'checkpoint.pt')));
  for(const [k,file] of [['trainerSourceSha256','train.py'],['batchingSourceSha256','batching.py'],])assert.equal(r[k],hash(path.join(root,file)));
  assert.equal(c.testUsed,false);assert.equal(c.selectedChildUpdates,r.bestStep);assert.equal(c.modelSha256,hash(path.join(d,'model.js')));
  assert.equal(c.policySha256,hash(path.join(root,'generation-policy.json')));
  const b=path.join(root,'initial-0'),s=read(path.join(b,'snapshot.json'));
  assert.equal(s.completedUpdates,0);assert.deepEqual(s.optimizerCounters,[]);assert.equal(s.additionalUpdates,false);
  assert.equal(s.checkpointSha256,hash(path.join(d,'checkpoint-0.pt')));
  assert.equal(r.parentSelectedWeightLineageUpdates,18000);assert.equal(s.parentSelectedWeightLineageUpdates,18000);
  assert.equal(r.parentCheckpointSha256,hash(path.resolve('training/language/round6/character-continue-10000/checkpoint.pt')));
  assert.equal(r.parameters,4537728);assert.equal(r.parentSelectedChildSteps,8000);
  assert.equal(r.experimentPolicySha256,hash(path.join(root,'experiment-policy.json')));
  assert.equal(s.gzipModelSha256,hash(path.join(b,'model.js.gz')));
  assert.equal(s.plainModelSha256,crypto.createHash('sha256').update(gunzipSync(fs.readFileSync(path.join(b,'model.js.gz')))).digest('hex'));
});

test('character comparisons preserve raw outputs, strict judgments and full Python/JS parity',()=>{
  const policy=read(path.join(root,'generation-policy.json'));
  for(const name of ['initial-0','expanded-characters-10000']) {
    const d=path.join(root,name),g=read(path.join(d,'validation.json')),v=read(path.join(d,'validation-review.json')),js=read(path.join(d,'validation-js.json'));
    assert.equal(g.maxNewTokens,192);assert.equal(g.partition,'validation');assert.equal(g.rows.length,13);
    assert.equal(g.policySha256,hash(path.join(root,'generation-policy.json')));
    assert.equal(v.generationSha256,hash(path.join(d,'validation.json')));assert.equal(v.independentHumanEvaluation,false);
    assert.equal(js.completeGenerationParity,true);assert.equal(js.modelSha256,g.modelFileSha256);
    for(const ref of js.references)assert.ok(ref.maxAbsoluteError<=2e-4);
    for(let i=0;i<13;i++) {
      const raw=g.rows[i],r=v.rows[i],p=policy.probes.validation[i];
      assert.equal(raw.id,p.id);assert.equal(raw.prefix,p.prefix);
      for(const k of ['id','text','tokens','eos','validUtf8','validTokens','inputTokens']) {
        assert.deepEqual(r[k],raw[k]);assert.deepEqual(js.rows[i][k],raw[k]);
      }
      const m=r.manual,total=['grammar','meaning','connection','repetition','breaks'].reduce((s,k)=>s+m[k],0);
      assert.equal(r.totalScore,total);assert.ok(m.reason.length>0);
      assert.equal(r.firstSentencePass,total>=9&&m.grammar===2&&m.connection===2&&m.sentenceClosed&&raw.validTokens);
    }
    assert.equal(v.passed,v.rows.filter(r=>r.firstSentencePass).length);
    for(const [name,group] of Object.entries(v.groups)) {
      const rows=v.rows.filter(r=>(r.site==='aozora')===(name==='narrative'));
      assert.equal(group.firstSentenceSuccessRate,rows.filter(r=>r.firstSentencePass).length/rows.length);
      assert.equal(group.fullOutputNonLoopRate,rows.filter(r=>!r.manual.fullOutputLoop).length/rows.length);
      assert.equal(group.gatePassed,group.firstSentenceSuccessRate>=.8&&group.fullOutputNonLoopRate>=.9);
    }
    const coreIds=new Set(read(path.resolve('training/language/round6/generation-policy.json')).probes.validation.map(p=>p.id));
    const core=v.rows.filter(r=>coreIds.has(r.id));assert.equal(v.coreTotal,9);assert.equal(v.corePassed,core.filter(r=>r.firstSentencePass).length);
    for(const [name,group] of Object.entries(v.coreGroups)){
      const rows=core.filter(r=>(r.site==='aozora')===(name==='narrative'));
      assert.equal(group.firstSentenceSuccessRate,rows.filter(r=>r.firstSentencePass).length/rows.length);
      assert.equal(group.fullOutputNonLoopRate,rows.filter(r=>!r.manual.fullOutputLoop).length/rows.length);
      assert.equal(group.gatePassed,group.firstSentenceSuccessRate>=.8&&group.fullOutputNonLoopRate>=.9);
    }
    assert.equal(v.gatePassed,[...Object.values(v.groups),...Object.values(v.coreGroups)].every(g=>g.gatePassed));
    assert.equal(fs.existsSync(path.join(d,'test.json')),false);
  }
  const c=read(path.join(root,'comparison.json'));assert.equal(c.fullMeaningPolicySha256,hash(path.join(root,'full-meaning-policy.json')));
  for(const name of ['initial-0','expanded-characters-10000']){
    const g=read(path.join(root,name,'validation-review.json')),coreIds=new Set(read(path.resolve('training/language/round6/generation-policy.json')).probes.validation.map(p=>p.id));
    for(const scope of ['expanded13','original9'])for(const genre of ['narrative','contemporary-expository']){
      const rows=g.rows.filter(r=>(scope==='expanded13'||coreIds.has(r.id))&&((r.site==='aozora')===(genre==='narrative'))),v=c.fullMeaningAssessment[name][scope+'/'+genre];
      assert.ok(rows.every(r=>typeof r.manual.fullOutputMeaningful==='boolean'));assert.equal(v.fullMeaningful,rows.filter(r=>r.manual.fullOutputMeaningful&&r.validTokens).length);assert.equal(v.rate,v.fullMeaningful/rows.length);assert.equal(v.criterionPassed,v.rate>=.8);
    }
  }
  assert.equal(c.naturalLanguageEstablished,c.languageGatePassed&&Object.values(c.fullMeaningAssessment['expanded-characters-10000']).every(v=>v.criterionPassed));
  assert.equal(c.testStillUnopened,true);assert.equal(c.publicModelReplaced,false);
});

test('character inventory binds artifacts and retains earlier experimental phases and MDN sources',()=>{
  const m=read(path.join(root,'reproducibility-manifest.json'));
  for(const f of m.files) {const p=path.join(root,f.path);assert.equal(hash(p),f.sha256,f.path);assert.equal(fs.statSync(p).size,f.bytes);assert.ok(f.bytes<100*1024*1024);}
  for(const [phase,info] of Object.entries(m.previousInventoriesVerified)) {
    const base=path.resolve('training/language',phase),file=path.join(base,info.manifestName||'reproducibility-manifest.json');
    assert.equal(info.manifestSha256,hash(file));const old=read(file);assert.equal(old.files.length,info.files);
    for(const f of old.files)assert.equal(hash(path.join(base,f.path)),f.sha256,f.path);
  }
  assert.equal(m.testStillUnopened,true);
  for(const k of ['externalWeights','externalTokenizer','externalInferenceAPI'])assert.equal(m[k],false);
});
