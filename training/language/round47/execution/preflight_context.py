"""Zero-update source/length/gold/gradient calibration; no optimizer instantiated."""
import pathlib,sys,json,hashlib,re,importlib.util,math
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));import train as t
from context_preference import load_pool,preference_loss
s=importlib.util.spec_from_file_location('own_tokenizer',R.parents[1]/'dialogue/tokenizer.py');enc=importlib.util.module_from_spec(s);s.loader.exec_module(enc)
t.torch.set_num_threads(2);t.torch.manual_seed(2049);p=t.read(R/'policy.json');pool=load_pool(R/p['contextPreference']['pool'],p['contextPreference']['poolSha256']);tok=t.read(R/'multiview/tokenizer.json')
source={}
with (R/'sources/documents.jsonl').open() as f:
 for line in f:
  d=json.loads(line)
  if d['id'].startswith('realpersona:'):source[d['id']]=d
cache={}
def turns(doc):
 if doc not in cache:
  d=source[doc];assert d['partition']=='train';raw=(pathlib.Path('/workspace/daily-conversation-source-audit/human-only-raw/train')/pathlib.Path(d['sourcePath']).name).read_bytes();assert hashlib.sha256(raw).hexdigest()==d['sourceSha256'];cache[doc]=[u['text'] for u in json.loads(raw)['utterances']];assert '\n'.join(cache[doc])==d['text']
 return cache[doc]
for r in pool:
 u=turns(r['document']);w=turns(r['wrongDocument']);assert r['prefix']=='\n'.join(u[r['turn']-2:r['turn']])+'\n' and r['target']==u[r['turn']];assert r['wrongPrefix']=='\n'.join(w[r['wrongTurn']-2:r['wrongTurn']])+'\n'
 anchors=(set(re.findall('[一-龯]{3,}',r['prefix'])) & set(re.findall('[一-龯]{3,}',r['target'])))-{'大丈夫','気分的'};assert sorted(anchors)==r['anchors'] and not any(z in r['wrongPrefix'] for z in anchors)
 for key,text in [('prefixTokens','prefix'),('wrongPrefixTokens','wrongPrefix'),('targetTokens','target')]:assert enc.encode_stream(r[text],tok)==r[key]
 assert enc.encode_stream(r['prefix']+r['target'],tok)==r['prefixTokens']+r['targetTokens'];assert enc.encode_stream(r['wrongPrefix']+r['target'],tok)==r['wrongPrefixTokens']+r['targetTokens']
cp=t.torch.load(R.parent/'round28/continue-10000/checkpoint.pt',map_location='cpu',weights_only=False);m=t.Decoder(cp['config']);t.initialize(m,tok);m.train();i,v=t.load_partition(R/'multiview','train');rows=[next(r for r in i['rows'] if r['site']=='human-chat' and r['variant']==k) for k in range(3)];x,y=t.pack(rows,v,256);ce=t.F.cross_entropy(m(x).reshape(-1,m.config['vocabulary']),y.reshape(-1));ce.backward();norm=lambda:math.sqrt(sum(float((q.grad.detach().double()**2).sum()) for q in m.parameters() if q.grad is not None));base=norm();m.zero_grad(set_to_none=True);before=t.torch.get_rng_state().clone();loss,rec=preference_loss(m,pool,0,batch=2);loss.backward();aux=norm();assert all(q.grad is not None and t.torch.isfinite(q.grad).all() for q in m.parameters()) and aux>0;assert t.torch.equal(before,t.torch.get_rng_state()) and m.training
report=dict(actualOptimizerUpdates=0,poolPairs=len(pool),positiveDocuments=len(set(r['document'] for r in pool)),allOriginalUtteranceObjectsAndSourceShasVerified=True,allGoldAndPrefixTokenizationAndConcatenationVerified=True,allDifferentDocumentSameLengthAndAvailableAnchorExclusionVerified=True,allTrainOnly=True,reservedTestRead=False,optimizerInstantiated=False,coefficientFixedBeforeGradients=p['contextPreference']['coefficient'],coefficientSearchPerformed=False,auxGradientNorm=aux,referenceHumanCeGradientNorm=base,weightedAuxToReferenceCeGradientRatio=p['contextPreference']['coefficient']*aux/base,referenceCeBatchSize=3,referenceIsNotFullCompositeTrainingGradient=True,initialAuxLoss=float(loss.detach()),initialAuxRecord=rec,allParameterGradientsFinite=True,dropoutRngAndModelModeExactlyRestored=True,limitations=['Same1024 pairs/403 documents asR46; pool unchanged, not whole conversation corpus','Gradient ratio on one2-pair batch versus a3-row CE batch is not late-training or all-pool calibration','Correct-context CE and diagnostic gain do not certify free-generation semantics'])
t.write(R/'execution/context-preflight.json',report);print(json.dumps(report),flush=True)
