"""Exact inverse trainer patch and all positive data equality; zero optimizer steps."""
import pathlib,json,hashlib,ast
R=pathlib.Path(__file__).resolve().parents[1];P=R.parent/'round34';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());rows=[]
for dirname in ['multiview','sources','prospective-daily-source']:
 for p in sorted((P/dirname).rglob('*')):
  if p.is_file()and '__pycache__'not in p.parts:
   rel=p.relative_to(P);assert sha(p)==sha(R/rel),str(rel);rows.append(dict(path=str(rel),sha256=sha(p),bytes=p.stat().st_size))
for n in ['batching.py','initialization.py','objective.py','sequence_objective.py','rollout_trace.py','source-policy.json','prefix_selection.py','human-turn-token-boundaries.json']:assert sha(P/n)==sha(R/n),n
original=read(P/'policy.json');new=read(R/'policy.json')
for k in ['sourceHashes','genreSampling','learningRate','seed','views','validationViews','unlikelihood','sequenceUnlikelihood','humanNegativePrefix','parentCheckpointSha256','parentManifestSha256','parentOptimizerUpdates','parentLatestWeightLineageUpdates','preparedPolicySha256']:assert original[k]==new[k],k
s=(R/'train.py').read_text().replace('\nfrom utterance_end_objective import eligible_mask, end_eos_loss','')
s=s.replace("    assert tok['bytes'][16]=='0a' and tok['bytes'][2]=='' and policy['humanUtteranceEndEos']['coefficient']==1.0\n",'')
s=s.replace("    settings['humanUtteranceEndEos']=policy['humanUtteranceEndEos']\n",'').replace('same raw targets + 1.0 EOS auxiliary only at original unmasked standalone-newline human TRAIN true utterance ends','same raw targets')
s=s.replace(';end_eos_positions=0;end_eos_batches=0','').replace(";end_eos_positions=saved['endEosPositions'];end_eos_batches=saved['endEosBatches']",'')
s=s.replace(',endEosPositions=end_eos_positions,endEosBatches=end_eos_batches','').replace('def objective(x,y,end_mask):','def objective(x,y):')
s=s.replace("            aux=end_eos_loss(logits,y,end_mask,eos_id=2)\n            return ce+1.0*ul+policy['humanUtteranceEndEos']['coefficient']*aux,ce.detach(),ul.detach(),count,aux.detach()",'            return ce+1.0*ul,ce.detach(),ul.detach(),count')
s=s.replace('end_mask=eligible_mask(rows,y,prefix_selector.ends,newline_id=16)\n        loss,ce_loss,ul_loss,negative_count,end_eos_loss_value=train_objective(x,y,end_mask)','loss,ce_loss,ul_loss,negative_count=train_objective(x,y)')
s=s.replace(';end_eos_positions+=int(end_mask.sum());end_eos_batches+=int(end_mask.any())','').replace(',endEosLoss=float(end_eos_loss_value),endEosPositionsThisBatch=int(end_mask.sum())','')
assert s==(P/'train.py').read_text(),'Trainer differs beyond explicit EOS loss, eligibility and resumable diagnostics'
# The integrated mathematical functions equal the prospectively tested prototypes by AST.
a=ast.parse((R/'utterance_end_objective.py').read_text());b=ast.parse((R/'execution/prospective-eos-objective/utterance_end_objective.py').read_text());assert [ast.dump(x)for x in a.body if isinstance(x,ast.FunctionDef)]==[ast.dump(x)for x in b.body if isinstance(x,ast.FunctionDef)]
# Prevent the previous trial's source evaluator allowlist failure before ANY training.
t=(R/'fixed-source-mrmp-dev/evaluate.py').read_text();assert "R.parent/'round34/continue-10000/model.js'"in t and "round28/continue-10000/model.js"not in t and "round33/continue-10000/model.js"not in t
out=dict(actualOptimizerUpdates=0,scientificComparator='round34',initializationParent='round28',adoptionAnchor='round25',oneLearningFactor='Additional true-human-utterance-end EOS auxiliary coefficient1.0',allPositiveDataByteidentical=rows,trainerReversePatchExactlyEqualsControl=True,existingNegativePrefixPolicyAndAllObjectivesCoefficientsLrSeedViewsAndInitialStateUnchanged=True,integratedObjectiveFunctionsExactlyMatchTestedPrototype=True,fixedSourceEvaluatorAllowlistProspectivelyCorrect=True,originalGoldTargetsPreserved=True,noModelForwardOrOptimizer=True)
(R/'execution/single-factor-audit.json').write_text(json.dumps(out,indent=2)+'\n');print('Single-factor exact; positive files',len(rows),'actual new optimizer updates0')
