import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {gunzipSync} from 'node:zlib';
const root=path.resolve('training/language/round5');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');

test('own character run binds actual updates, source identities and saved comparison',()=>{
  const d=path.join(root,'characters-10000'),r=read(path.join(d,'result.json'));
  const a=read(path.join(root,'optimizer-audit.json')),c=read(path.join(root,'checkpoint-choice.json'));
  assert.equal(r.completedRun,true);assert.equal(r.completedSteps,10000);assert.equal(r.requestedSteps,10000);
  assert.equal(a.actualOptimizerUpdates,10000);assert.deepEqual(a.optimizerStepCounters,[10000]);
  assert.equal(a.selectedWeightLineageUpdates,r.bestStep);assert.equal(a.baselineAddsUpdates,false);
  assert.equal(a.fullPrecisionWeightsAndOptimizer,true);assert.equal(a.pythonAndTorchRngSaved,true);
  assert.equal(r.randomInitialization,true);assert.equal(r.previousWeightsNotAllowed,true);assert.equal(r.wordMerges,0);
  for(const k of ['externalWeights','externalTokenizer','externalInferenceAPI'])assert.equal(r[k],false);
  assert.equal(r.checkpointSha256,hash(path.join(d,'checkpoint.pt')));
  for(const [k,file] of [['trainerSourceSha256','train.py'],['batchingSourceSha256','batching.py'],['characterFrequenciesSha256','character-frequencies.json'],['preparedDataSha256','unicode-bpe-4503/data.json']])assert.equal(r[k],hash(path.join(root,file)));
  assert.equal(c.testUsed,false);assert.equal(c.selectedStep,r.bestStep);assert.equal(c.modelSha256,hash(path.join(d,'model.js')));
  assert.equal(c.policySha256,hash(path.join(root,'generation-policy.json')));
  const b=path.join(root,'baseline-1000'),s=read(path.join(b,'snapshot.json'));
  assert.equal(s.actualOptimizerUpdates,1000);assert.deepEqual(s.optimizerStepCounters,[1000]);assert.equal(s.additionalUpdates,false);
  assert.equal(s.checkpointSha256,hash(path.join(d,'checkpoint-1000.pt')));
  assert.equal(s.gzipModelSha256,hash(path.join(b,'model.js.gz')));
  assert.equal(s.plainModelSha256,crypto.createHash('sha256').update(gunzipSync(fs.readFileSync(path.join(b,'model.js.gz')))).digest('hex'));
});

test('character comparisons preserve raw outputs, strict judgments and full Python/JS parity',()=>{
  const policy=read(path.join(root,'generation-policy.json'));
  for(const name of ['baseline-1000','characters-10000']) {
    const d=path.join(root,name),g=read(path.join(d,'validation.json')),v=read(path.join(d,'validation-review.json')),js=read(path.join(d,'validation-js.json'));
    assert.equal(g.maxNewTokens,192);assert.equal(g.partition,'validation');assert.equal(g.rows.length,9);
    assert.equal(g.policySha256,hash(path.join(root,'generation-policy.json')));
    assert.equal(v.generationSha256,hash(path.join(d,'validation.json')));assert.equal(v.independentHumanEvaluation,false);
    assert.equal(js.completeGenerationParity,true);assert.equal(js.modelSha256,g.modelFileSha256);
    for(const ref of js.references)assert.ok(ref.maxAbsoluteError<=2e-4);
    for(let i=0;i<9;i++) {
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
    assert.equal(v.gatePassed,Object.values(v.groups).every(g=>g.gatePassed));
    assert.equal(fs.existsSync(path.join(d,'test.json')),false);
  }
  const c=read(path.join(root,'comparison.json'));assert.equal(c.testStillUnopened,true);assert.equal(c.publicModelReplaced,false);
});

test('character inventory binds artifacts and retains both earlier experimental phases',()=>{
  const m=read(path.join(root,'reproducibility-manifest.json'));
  for(const f of m.files) {const p=path.join(root,f.path);assert.equal(hash(p),f.sha256,f.path);assert.equal(fs.statSync(p).size,f.bytes);assert.ok(f.bytes<100*1024*1024);}
  for(const [phase,info] of Object.entries(m.previousInventoriesVerified)) {
    const base=path.resolve('training/language',phase),file=path.join(base,'reproducibility-manifest.json');
    assert.equal(info.manifestSha256,hash(file));const old=read(file);assert.equal(old.files.length,info.files);
    for(const f of old.files)assert.equal(hash(path.join(base,f.path)),f.sha256,f.path);
  }
  assert.equal(m.testStillUnopened,true);
  for(const k of ['externalWeights','externalTokenizer','externalInferenceAPI'])assert.equal(m[k],false);
});
