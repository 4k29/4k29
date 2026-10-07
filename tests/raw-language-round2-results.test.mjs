import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const root=path.resolve('training/language/round2');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');

test('both completed raw runs and the selected candidate bind real optimizer records',()=>{
  const audit=read(path.join(root,'optimizer-audit.json'));
  assert.equal(audit.totalCompletedCleanRawUpdates,22000);
  assert.equal(audit.discardedPrecisionTimingUpdates,60);
  for(const run of audit.runs) {
    const dir=path.join(root,run.run),result=read(path.join(dir,'result.json'));
    assert.equal(result.completedSteps,result.requestedSteps);
    assert.equal(result.completedSteps,run.completedOptimizerUpdates);
    assert.equal(result.completedRun,true);
    assert.equal(result.checkpointSha256,hash(path.join(dir,'checkpoint.pt')));
    assert.equal(run.modelSha256,hash(path.join(dir,'model.js')));
    assert.deepEqual(run.optimizerStepCounters,[result.completedSteps]);
    assert.equal(run.fullPrecisionWeightsAndOptimizer,true);
    assert.equal(run.pythonAndTorchRngSaved,true);
  }
  const choice=read(path.join(root,'checkpoint-choice.json'));
  const winner=choice.candidates.reduce((a,b)=>a.validationNllPerUtf8Byte<=b.validationNllPerUtf8Byte?a:b);
  assert.equal(choice.chosenRun,winner.run);assert.equal(choice.testUsed,false);
  assert.equal(choice.policySha256,hash(path.join(root,'generation-policy.json')));
  for(const c of choice.candidates) {
    assert.equal(c.resultSha256,hash(path.join(root,c.run,'result.json')));
    assert.equal(c.modelSha256,hash(path.join(root,c.run,'model.js')));
  }
  const child=read(path.join(root,'prefix-million/result.json'));
  assert.equal(child.parentCheckpointSha256,hash(path.join(root,'raw-modern-million/checkpoint.pt')));
  assert.equal(child.ownParentOnly,true);assert.equal(child.optimizerReset,true);
  assert.equal(child.externalWeights,false);
});

test('paired fresh raw TEST and strict manual language judgments remain complete and unedited',()=>{
  const policy=read(path.join(root,'generation-policy.json'));
  const comparison=read(path.join(root,'comparison.json'));
  const selected=path.join(root,comparison.candidate.run);
  for(const [dir,reviewName] of [[selected,'review-test.json'],[path.join(root,'baseline'),'test-review.json']]) {
    const gen=read(path.join(dir,'test.json')),review=read(path.join(dir,reviewName)),js=read(path.join(dir,'test-js.json'));
    assert.equal(gen.partition,'test');assert.equal(gen.rows.length,24);
    assert.equal(gen.policySha256,hash(path.join(root,'generation-policy.json')));
    assert.equal(review.generationSha256,hash(path.join(dir,'test.json')));
    assert.equal(review.independentHumanEvaluation,false);
    assert.equal(js.completeGenerationParity,true);assert.equal(js.modelSha256,gen.modelFileSha256);
    for(const ref of js.references)assert.ok(ref.maxAbsoluteError<=0.0002);
    for(let i=0;i<24;i++) {
      const g=gen.rows[i],r=review.rows[i],p=policy.probes.test[i];
      assert.equal(g.id,p.id);assert.equal(g.document,p.document);assert.equal(g.prefix,p.prefix);
      for(const k of ['text','tokens','eos','validUtf8','validTokens','inputTokens']) {
        assert.deepEqual(r[k],g[k]);assert.deepEqual(js.rows[i][k],g[k]);
      }
      const m=r.manual,score=['grammar','meaning','connection','repetition','breaks'].reduce((s,k)=>s+m[k],0);
      assert.equal(r.totalScore,score);
      assert.equal(r.firstSentencePass,score>=9&&m.grammar===2&&m.connection===2&&m.sentenceClosed&&g.validTokens);
      assert.ok(m.reason.length>0);
    }
    assert.equal(review.passed,review.rows.filter(r=>r.firstSentencePass).length);
    for(const [name,group] of Object.entries(review.groups)) {
      const rows=review.rows.filter(r=>(r.site==='aozora')===(name==='narrative'));
      const rate=rows.filter(r=>r.firstSentencePass).length/rows.length;
      const nonLoop=rows.filter(r=>!r.manual.fullOutputLoop).length/rows.length;
      assert.equal(group.firstSentenceSuccessRate,rate);assert.equal(group.fullOutputNonLoopRate,nonLoop);
      assert.equal(group.gatePassed,rate>=.8&&nonLoop>=.9);
    }
    assert.equal(review.gatePassed,Object.values(review.groups).every(g=>g.gatePassed));
  }
  assert.equal(comparison.publicModelReplaced,false);
  assert.equal(comparison.testNowConsumed,true);
});

test('new reproducibility inventory binds every recorded artifact and shared own implementation',()=>{
  const manifest=read(path.join(root,'reproducibility-manifest.json'));
  for(const f of manifest.files) {
    const p=path.join(root,f.path);assert.equal(hash(p),f.sha256,f.path);
    assert.equal(fs.statSync(p).size,f.bytes);assert.ok(f.bytes<100*1024*1024);
  }
  for(const f of manifest.sharedFiles)assert.equal(hash(path.resolve(f.path)),f.sha256,f.path);
  assert.equal(manifest.priorFrozenFilesVerified,206);
  assert.equal(manifest.externalWeights,false);assert.equal(manifest.externalTokenizer,false);
  assert.equal(manifest.externalInferenceAPI,false);
});
