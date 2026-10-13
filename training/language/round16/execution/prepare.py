from pathlib import Path
import shutil,json,hashlib,torch
B=Path('/workspace/4k29/training/language');R=B/'round16';S=B/'round13';R.mkdir(exist_ok=False);(R/'execution').mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
cp=B/'round11/continue-10000/checkpoint.pt';parent=torch.load(cp,map_location='cpu',weights_only=False)
assert parent['step']==10000 and parent['beststep']==9500
lr=parent['optimizer']['param_groups'][0]['lr'];assert abs(lr-.0000225)<1e-18
for name in ['train.py','batching.py']:
 shutil.copy2(S/name,R/name)
(R/'initialization.py').write_text('''"""Restore our own latest optimizer-aligned Round11 weights; no foreign models."""
import hashlib,json,pathlib,torch
ROOT=pathlib.Path(__file__).resolve().parent
PARENT=ROOT.parent/'round11'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def initialize(model,tokenizer,ancestor=None):
    policy=json.loads((ROOT/'policy.json').read_text())
    manifest=PARENT/'execution/artifact-manifest.json'
    assert sha(manifest)==policy['parentManifestSha256']
    for row in json.loads(manifest.read_text())['files']:
        assert sha(PARENT/row['path'])==row['sha256'],row['path']
    cp=PARENT/'continue-10000/checkpoint.pt'
    assert sha(cp)==policy['parentCheckpointSha256']
    saved=torch.load(cp,map_location='cpu',weights_only=False)
    assert saved['step']==10000 and saved['config']==model.config
    assert sorted(set(int(s['step']) for s in saved['optimizer']['state'].values()))==[10000]
    assert sha(PARENT/'multiview/tokenizer.json')==policy['sourceHashes']['word-bpe-512/tokenizer.json']
    model.load_state_dict(saved['model'],strict=True)
    assert all(torch.isfinite(p).all() for p in model.parameters())
    return dict(parentCheckpointSha256=sha(cp),parentSelectedLineageUpdates=49000,parentWeightSelection='Latest optimizer-aligned state, not beststate',parentOptimizerUpdates=10000,parentSeenTargetTokens=saved['seen_tokens'],parentSeenTargetUtf8Bytes=saved['seen_bytes'],initialization='Our Round11 latest model + AdamW moments + Torch/Python RNG; hold terminal learning rate',externalWeights=False)
''')
p=R/'train.py';s=p.read_text()
s=s.replace("args.lr!=.00015", "args.lr!=policy['learningRate']")
needle="model=Decoder(config);initialization=initialize(model,tok,args.ancestor);optimizer=torch.optim.AdamW(model.parameters(),lr=args.lr,weight_decay=.05)"
assert needle in s
s=s.replace(needle,needle+"\n    parent_state=torch.load(ROOT.parent/'round11/continue-10000/checkpoint.pt',map_location='cpu',weights_only=False)\n    optimizer.load_state_dict(parent_state['optimizer']);torch.set_rng_state(parent_state['torchRng']);rng.setstate(parent_state['pythonRng'])")
needle="        warmup=min(250,max(50,args.steps//10));schedule=step/warmup if step<=warmup else .15+.85*.5*(1+math.cos(math.pi*(step-warmup)/max(1,args.steps-warmup)))\n        for group in optimizer.param_groups:group['lr']=args.lr*schedule"
assert needle in s;s=s.replace(needle,"        for group in optimizer.param_groups:group['lr']=args.lr")
s=s.replace("settings['savedComparisonSnapshotStep']=0", "settings['savedComparisonSnapshotStep']=0;settings['schedule']='Hold exact Round11 terminal LR throughout additional10000; preserve moments and RNG, no restart'")
p.write_text(s)
policy=json.loads((S/'policy.json').read_text());policy.update(parentManifestSha256=sha(B/'round11/execution/artifact-manifest.json'),parentCheckpointSha256=sha(cp),genreSampling=parent['settings']['genreSampling'],learningRate=lr,parentLatestWeightLineageUpdates=49000,parentOptimizerUpdates=10000,parentStateSelection='Latest aligned model/optimizer/RNG, not selected best weights with latest moments',optimizerContinuation=True,experiment='Round16 prospective additional-duration control: restore Round11 latest aligned state; retain original genres, views, vocabulary and architecture; hold exact terminal LR, no warmup/restart',nllSuccessThreshold=0.9788898793272423,meaningGatePolicySha256=sha(B/'round10/full-meaning-policy.json'),schedule={'kind':'constant_existing_terminal_value','learningRate':lr,'additionalUpdates':10000},rationale={'evidence':'Round11 common NLL decreased .9860957037 at7000 to .9788898793 at9500, latest10000 .9789190007; fresh genre resampling controls13/14 did not beat control or full meaning. Additional duration at retained terminal LR isolates continued optimization without resetting moments/RNG.','limitations':'No new source diversity, no proof of language improvement from NLL; original ten-thousand-step cosine was not defined beyond its end, so this prospective extension holds its exact terminal value.'})
policy['codeHashes']={f:sha(R/f) for f in ['train.py','batching.py','initialization.py']};write(R/'policy.json',policy)
man=json.loads((S/'source-manifest.json').read_text())
paths=[r['path'] for r in man['files']]
paths += ['../round11/execution/artifact-manifest.json','../round11/continue-10000/checkpoint.pt','../round11/continue-10000/result.json','../round11/continue-10000/model.js']
man['files']=[{'path':f,'sha256':sha(R/f),'bytes':(R/f).stat().st_size} for f in dict.fromkeys(paths)];write(R/'source-manifest.json',man)
helpers=['audit.py','check_sampling.py','compare.sh','rebind_old.py','replay_sampler.py','verify_runtime.py','summarize.py','check_export_rounding.py','diagnose_parity.py','diagnose_parity.mjs','diagnose_generation.py','diagnose_gap.py','freeze_results.py','verify_manifest.py']
for f in helpers:
 s=(S/'execution'/f).read_text().replace('round13','round16') if f=='compare.sh' else (S/'execution'/f).read_text()
 (R/'execution'/f).write_text(s)
p=R/'execution/audit.py';s=p.read_text()
s=s.replace("assert zero['step']==0 and not zero['optimizer']['state'] and zero['seen_tokens']==zero['seen_bytes']==0", "assert zero['step']==0 and zero['optimizer']['state'] and zero['seen_tokens']==zero['seen_bytes']==0")
s=s.replace("parent=torch.load(PARENT/'word-512-continue-10000/checkpoint.pt'", "parent=torch.load(ROOT.parent/'round11/continue-10000/checkpoint.pt'")
s=s.replace("parent['beststate'][k]", "parent['model'][k]")
s=s.replace("assert counters==[cp['step']]", "assert counters==[10000+cp['step']]")
s=s.replace("selectedWeightLineageUpdates=39000+cp['beststep'],latestWeightLineageUpdates=39000+cp['step']", "selectedWeightLineageUpdates=49000+cp['beststep'],latestWeightLineageUpdates=49000+cp['step'],parentOptimizerUpdates=10000")
s=s.replace("assert cp['bestloss']==min", "assert zero['optimizer']['param_groups']==parent['optimizer']['param_groups']\nassert zero['pythonRng']==parent['pythonRng'] and torch.equal(zero['torchRng'],parent['torchRng'])\nfor key,state in zero['optimizer']['state'].items():\n for name,t in state.items():assert torch.equal(t,parent['optimizer']['state'][key][name])\nassert cp['bestloss']==min")
p.write_text(s)
p=R/'execution/replay_sampler.py';s=p.read_text().replace("rng=random.Random(cp['settings']['seed']);assert rng.getstate()==zero['pythonRng']", "rng=random.Random();rng.setstate(zero['pythonRng']);assert rng.getstate()==zero['pythonRng']");p.write_text(s)
p=R/'execution/verify_runtime.py';s=p.read_text().replace("saved=torch.load(PARENT/'word-512-continue-10000/checkpoint.pt'", "saved=torch.load(ROOT.parent/'round11/continue-10000/checkpoint.pt'");p.write_text(s)
(R/'execution/run.sh').write_text(f'''#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../../../.."
python training/language/round16/train.py --merges 512 --steps 10000 --dim 192 --layers 8 --heads 4 --batch 8 --threads 2 --seed 2049 --lr {lr!r} --validation-every 500 --run continue-10000 --precision float32 "$@"
''')
(R/'.gitattributes').write_bytes((S/'.gitattributes').read_bytes())
(R/'README.md').write_text('''# Round 16 — optimizerとRNGを保持した追加学習

Round 11最新step10000の重み・AdamW moment・Torch/Python RNGから追加10,000更新。採用step9500のbeststateと最新optimizerを混ぜない。ジャンル45/10/10/15/10/2.5/5/2.5%、通常/Glyph/文字境界40/30/30、8層dim192、独自語彙・原文・fold・context256を保持。既存cosineの終端値を追加区間で固定する拡張規則を事前に定義し、warmup・optimizer・RNGを再初期化しない。

Round 11で7000→9500のNLLが改善を続けていたことを追加学習の根拠にした。語彙・モデル容量・データの多様性を増やした実験ではない。共通開発NLLが0.9788898793272423を下回る、または既存の厳格な言語ゲートを合格することが今回の進捗目標。NLLのみの改善を日本語能力の改善とは呼ばない。TEST生成・公開モデル交換は禁止。

新規実行: `bash training/language/round16/execution/run.sh`。未完了のcheckpointからだけ、同commandに`--resume`を付ける。完了済み実験は再開せず、audit/verify_manifestで確認する。実更新数とoptimizer counterには親の10000更新との差があるため、RESULTS.mdで区別する。
''')
shutil.copy2('/tmp/prepare_round16.py',R/'execution/prepare.py')
print(json.dumps({'preparedRound':16,'actualOptimizerUpdates':0,'parentCheckpointSha256':sha(cp),'parentOptimizerUpdates':10000,'frozenConstantLearningRate':lr}))
