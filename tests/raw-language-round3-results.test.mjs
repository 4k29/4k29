import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {gunzipSync} from 'node:zlib';
const root=path.resolve('training/language/round3');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');

test('completed raw learning binds real optimizer counters and same-run snapshot',()=>{
  const audit=read(path.join(root,'optimizer-audit.json'));
  assert.equal(audit.totalCompletedCleanRawUpdates,12000);
  assert.equal(audit.mainRunUpdates,10000);
  assert.equal(audit.diagnosticSnapshotAddsUpdates,false);
  assert.equal(audit.midpointDiagnosticAddsUpdates,false);
  assert.equal(audit.midpointWeightsOnlyNotResumable,true);
  assert.equal(audit.unknownUnsavedUpdatesNotCounted,true);
  for(const run of audit.runs) {
    const dir=path.join(root,run.run),result=read(path.join(dir,'result.json'));
    assert.equal(result.completedSteps,result.requestedSteps);
    assert.equal(result.completedSteps,run.completedOptimizerUpdates);
    assert.equal(result.completedRun,true);
    assert.equal(hash(path.join(dir,'checkpoint.pt')),result.checkpointSha256);
    assert.equal(hash(path.join(dir,'model.js')),run.modelSha256);
    assert.deepEqual(run.optimizerStepCounters,[result.completedSteps]);
    assert.equal(run.fullPrecisionWeightsAndOptimizer,true);
    assert.equal(run.pythonAndTorchRngSaved,true);
    assert.equal(result.randomInitialization,true);
    assert.equal(result.previousWeightsNotAllowed,true);
  }
  const snapshot=read(path.join(root,'baseline-1000/snapshot.json'));
  assert.equal(snapshot.actualOptimizerUpdates,1000);
  assert.equal(snapshot.additionalUpdates,false);
  assert.equal(snapshot.checkpointSha256,hash(path.join(root,'raw-chains-10000/checkpoint-1000.pt')));
  const baselinePacked=path.join(root,'baseline-1000/model.js.gz');
  assert.equal(snapshot.gzipModelSha256,hash(baselinePacked));
  assert.equal(snapshot.plainModelSha256,crypto.createHash('sha256').update(gunzipSync(fs.readFileSync(baselinePacked))).digest('hex'));
  const choice=read(path.join(root,'checkpoint-choice.json'));
  assert.equal(choice.testUsed,false);
  assert.equal(choice.policySha256,hash(path.join(root,'generation-policy.json')));
  assert.equal(choice.modelSha256,hash(path.join(root,'raw-chains-10000/model.js')));
  const mid=read(path.join(root,'midpoint-validation-diagnostic.json'));
  const review=read(path.join(root,'midpoint-diagnostic-review.json'));
  assert.equal(mid.checkpointCompletedUpdates,5000);assert.equal(mid.notFinalWeightSelection,true);
  assert.equal(mid.retainedWeightsSha256,hash(path.join(root,mid.retainedFullPrecisionWeights)));
  assert.equal(mid.reproductionScriptSha256,hash(path.join(root,mid.reproductionScript)));
  assert.equal(mid.reproducedWithRetainedFullPrecisionState,true);
  assert.equal(review.generationSha256,hash(path.join(root,'midpoint-validation-diagnostic.json')));
  assert.equal(review.total,9);assert.equal(review.passed,0);assert.equal(review.fullOutputNonLoop,1);
});

test('development continuations and strict judgments preserve every generated token',()=>{
  const policy=read(path.join(root,'generation-policy.json'));
  for(const name of ['raw-chains-10000','baseline-1000']) {
    const dir=path.join(root,name),gen=read(path.join(dir,'validation.json'));
    const review=read(path.join(dir,'validation-review.json')),js=read(path.join(dir,'validation-js.json'));
    assert.equal(gen.partition,'validation');assert.equal(gen.rows.length,9);
    assert.equal(gen.policySha256,hash(path.join(root,'generation-policy.json')));
    assert.equal(review.generationSha256,hash(path.join(dir,'validation.json')));
    assert.equal(review.independentHumanEvaluation,false);
    assert.equal(js.completeGenerationParity,true);assert.equal(js.modelSha256,gen.modelFileSha256);
    for(const ref of js.references)assert.ok(ref.maxAbsoluteError<=2e-4);
    for(let i=0;i<9;i++) {
      const raw=gen.rows[i],judged=review.rows[i],original=policy.probes.validation[i];
      assert.equal(raw.id,original.id);assert.equal(raw.prefix,original.prefix);
      for(const key of ['id','text','tokens','eos','validUtf8','validTokens','inputTokens']) {
        assert.deepEqual(raw[key],judged[key]);assert.deepEqual(raw[key],js.rows[i][key]);
      }
      const m=judged.manual,score=['grammar','meaning','connection','repetition','breaks'].reduce((s,k)=>s+m[k],0);
      assert.equal(judged.totalScore,score);
      assert.equal(judged.firstSentencePass,score>=9&&m.grammar===2&&m.connection===2&&m.sentenceClosed&&raw.validTokens);
      assert.ok(m.reason.length>0);
    }
    for(const [name,g] of Object.entries(review.groups)) {
      const rows=review.rows.filter(r=>(r.site==='aozora')===(name==='narrative'));
      assert.equal(g.firstSentenceSuccessRate,rows.filter(r=>r.firstSentencePass).length/rows.length);
      assert.equal(g.fullOutputNonLoopRate,rows.filter(r=>!r.manual.fullOutputLoop).length/rows.length);
      assert.equal(g.gatePassed,g.firstSentenceSuccessRate>=.8&&g.fullOutputNonLoopRate>=.9);
    }
    assert.equal(review.gatePassed,Object.values(review.groups).every(g=>g.gatePassed));
    assert.equal(fs.existsSync(path.join(dir,'test.json')),false);
  }
  const comparison=read(path.join(root,'comparison.json'));
  assert.equal(comparison.testStillUnopened,true);
  assert.equal(comparison.publicModelReplaced,false);
});

test('round3 inventory preserves actual artifacts, shared code and previous experiments',()=>{
  const m=read(path.join(root,'reproducibility-manifest.json'));
  for(const f of m.files) {
    const p=path.join(root,f.path);assert.equal(hash(p),f.sha256,f.path);
    assert.equal(fs.statSync(p).size,f.bytes);assert.ok(f.bytes<100*1024*1024);
  }
  for(const f of m.sharedFiles)assert.equal(hash(path.resolve(f.path)),f.sha256,f.path);
  assert.deepEqual(m.priorInventories.map(p=>p.verifiedFiles),[206,145]);
  assert.equal(m.externalWeights,false);assert.equal(m.externalTokenizer,false);
  assert.equal(m.externalInferenceAPI,false);assert.equal(m.testStillUnopened,true);
});
