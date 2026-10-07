import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {gunzipSync} from 'node:zlib';
const root=path.resolve('training/language/round4');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');

test('completed boundary continuation binds real updates, own parent and selected weights',()=>{
  const audit=read(path.join(root,'optimizer-audit.json')),dir=path.join(root,'boundary-focus-2000');
  const r=read(path.join(dir,'result.json')),choice=read(path.join(root,'checkpoint-choice.json'));
  assert.equal(r.completedRun,true);assert.equal(r.completedSteps,2000);assert.equal(r.requestedSteps,2000);
  assert.equal(audit.actualAdditionalOptimizerUpdates,2000);assert.deepEqual(audit.optimizerStepCounters,[2000]);
  assert.equal(audit.selectedWeightLineageUpdates,r.parentSelectedSteps+r.bestStep);
  assert.equal(audit.diagnosticTerminalAddsUpdates,false);
  assert.equal(audit.fullPrecisionWeightsAndOptimizer,true);assert.equal(audit.pythonAndTorchRngSaved,true);
  assert.equal(r.parentCheckpointSha256,hash(path.resolve('training/language/round3/raw-chains-10000/checkpoint.pt')));
  assert.equal(r.checkpointSha256,hash(path.join(dir,'checkpoint.pt')));
  assert.equal(r.trainerSourceSha256,hash(path.join(root,'train.py')));
  assert.equal(r.batchingSourceSha256,hash(path.join(root,'batching.py')));
  assert.equal(r.ownParentOnly,true);assert.equal(r.optimizerReset,true);assert.equal(r.seedReset,true);
  assert.equal(choice.testUsed,false);assert.equal(choice.modelSha256,hash(path.join(dir,'model.js')));
  assert.equal(choice.policySha256,hash(path.join(root,'generation-policy.json')));
  const snap=read(path.join(root,'terminal-2000/snapshot.json'));
  assert.equal(snap.additionalUpdates,false);assert.equal(snap.actualTerminalUpdates,2000);
  const packed=path.join(root,'terminal-2000/model.js.gz');assert.equal(snap.gzipModelSha256,hash(packed));
  assert.equal(snap.plainModelSha256,crypto.createHash('sha256').update(gunzipSync(fs.readFileSync(packed))).digest('hex'));
});

test('unaltered development outputs preserve strict scores, invalid UTF8 and full parity',()=>{
  const policy=read(path.join(root,'generation-policy.json'));
  for(const name of ['boundary-focus-2000','terminal-2000']) {
    const dir=path.join(root,name),gen=read(path.join(dir,'validation.json'));
    const review=read(path.join(dir,'validation-review.json')),js=read(path.join(dir,'validation-js.json'));
    assert.equal(gen.partition,'validation');assert.equal(gen.rows.length,9);
    assert.equal(gen.policySha256,hash(path.join(root,'generation-policy.json')));
    assert.equal(review.generationSha256,hash(path.join(dir,'validation.json')));
    assert.equal(review.independentHumanEvaluation,false);assert.equal(js.completeGenerationParity,true);
    assert.equal(js.modelSha256,gen.modelFileSha256);
    for(const ref of js.references)assert.ok(ref.maxAbsoluteError<=2e-4);
    for(let i=0;i<9;i++) {
      const g=gen.rows[i],r=review.rows[i],p=policy.probes.validation[i];
      assert.equal(g.id,p.id);assert.equal(g.prefix,p.prefix);
      for(const k of ['id','text','tokens','eos','validUtf8','validTokens','inputTokens']) {
        assert.deepEqual(r[k],g[k]);assert.deepEqual(js.rows[i][k],g[k]);
      }
      const m=r.manual,total=['grammar','meaning','connection','repetition','breaks'].reduce((s,k)=>s+m[k],0);
      assert.equal(r.totalScore,total);
      assert.equal(r.firstSentencePass,total>=9&&m.grammar===2&&m.connection===2&&m.sentenceClosed&&g.validTokens);
      assert.ok(m.reason.length>0);
    }
    assert.equal(review.passed,1);assert.equal(review.validTokenOutputs,8);
    assert.equal(review.gatePassed,false);
    for(const [name,g] of Object.entries(review.groups)) {
      const rows=review.rows.filter(r=>(r.site==='aozora')===(name==='narrative'));
      assert.equal(g.firstSentenceSuccessRate,rows.filter(r=>r.firstSentencePass).length/rows.length);
      assert.equal(g.fullOutputNonLoopRate,rows.filter(r=>!r.manual.fullOutputLoop).length/rows.length);
      assert.equal(g.gatePassed,g.firstSentenceSuccessRate>=.8&&g.fullOutputNonLoopRate>=.9);
    }
    assert.equal(fs.existsSync(path.join(dir,'test.json')),false);
  }
  const c=read(path.join(root,'comparison.json'));assert.equal(c.testStillUnopened,true);
  assert.equal(c.publicModelReplaced,false);assert.equal(c.terminalDiagnosticSameWeightsAsSelected,true);
});

test('new inventory binds raw focused data, all artifacts and the frozen own parent',()=>{
  const m=read(path.join(root,'reproducibility-manifest.json'));
  for(const f of m.files) {
    const p=path.join(root,f.path);assert.equal(hash(p),f.sha256,f.path);
    assert.equal(fs.statSync(p).size,f.bytes);assert.ok(f.bytes<100*1024*1024);
  }
  for(const f of m.sharedFiles)assert.equal(hash(path.resolve(f.path)),f.sha256,f.path);
  assert.equal(m.priorRoundFilesVerified,88);assert.equal(m.testStillUnopened,true);
  assert.equal(m.externalWeights,false);assert.equal(m.externalTokenizer,false);assert.equal(m.externalInferenceAPI,false);
  const parent=path.resolve('training/language/round3');assert.equal(m.priorRoundManifestSha256,hash(path.join(parent,'reproducibility-manifest.json')));
  const data=path.join(root,'boundary-bpe-8192');
  for(const name of ['tokenizer.json',...['validation','test'].flatMap(p=>[`${p}.index.json`,`${p}.tokens.bin`])]) {
    assert.equal(hash(path.join(data,name)),hash(path.join(parent,'raw-bpe-8192',name)));
  }
});
