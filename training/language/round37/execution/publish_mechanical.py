"""Save actual checkpoints and mechanical evidence to draft PR independently of chat.
Never invent language judgments, promote a model, or claim unseen/general ability.
"""
import pathlib,subprocess,json,hashlib,datetime,sys,torch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from checkpoint_chunks import pack
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';REPO=R.parents[2]
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def run(args,**kw):return subprocess.run(args,cwd=REPO,check=True,**kw)
status=int(sys.argv[1]);torch.set_num_threads(1);cp=R/'continue-10000/checkpoint.pt';saved=torch.load(cp,map_location='cpu',weights_only=False) if cp.exists() else None;step=saved['step'] if saved else 0;counters=sorted({int(s['step']) for s in saved['optimizer']['state'].values()}) if saved else [];assert not saved or counters==[20000+step]
model=R/'continue-10000/model.js';new=E/'new-validation.json';old=E/'old-validation.json';mechanical=all(p.exists() for p in [new,old,E/'new-validation-js.json',E/'old-validation-js.json',E/'sampler-replay.json'])
record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pipelineExitCode':status,'actualRetainedAdditionalUpdates':step,'requestedUpdates':10000,'optimizerCounters':counters,'completedTraining':step==10000,'mechanicalOutputsAvailable':mechanical,'languageAssessment':'Pending complete raw-output reading; no semantic score guessed','strictLanguageGateAssessed':False,'publicModelChanged':False,'testGenerated':False,'uncheckpointedPhysicalUpdatesUnknown':status!=0 and step<10000,'resumeCommand':'bash training/language/round37/execution/run.sh --resume >> training/language/round37/execution/train.log 2>&1' if step<10000 else None,'bestDevelopmentNllPerByte':saved['bestloss'] if saved else None,'selectedStep':saved['beststep'] if saved else None}
record['mechanicalScope']='Original17 generation/JS plus sampler replay'
record['supplementaryDailyGenerationAvailable']=all((E/n).exists() for n in ['daily-old-python.json','daily-new-python.json','daily-old-javascript.json','daily-new-javascript.json','daily-numerical-comparison.json'])
record['supplementaryDailyRoundingAvailable']=(E/'daily-rounding-comparison.json').exists()
record['supplementaryHumanDevelopmentLossAvailable']=(E/'daily-human-likelihood-comparison.json').exists()
record['allPlannedMechanicalOutputsAvailable']=mechanical and all(record[k] for k in ['supplementaryDailyGenerationAvailable','supplementaryDailyRoundingAvailable','supplementaryHumanDevelopmentLossAvailable'])
selected_audit=read(E/'selected-optimizer-audit.json') if (E/'selected-optimizer-audit.json').exists() else {}
record['selectedOptimizerArchiveVerified']=bool(saved and selected_audit.get('selectedFullStateAvailable') and selected_audit.get('actualRetainedTrialUpdates')==step and selected_audit.get('selectedStep')==saved['beststep'] and (R/'continue-10000/best-aligned-checkpoint.pt').exists() and hashlib.sha256((R/'continue-10000/best-aligned-checkpoint.pt').read_bytes()).hexdigest()==selected_audit.get('selectedCheckpointSha256'))
write(E/'mechanical-status.json',record)
(R/'MECHANICAL_STATUS.md').write_text('# Mechanical execution status — language review pending\n\n'+f"Actual retained additional optimizer updates: {step}/10000. Optimizer counters: {counters}. Pipeline exit: {status}. Mechanical outputs available: {mechanical}.\n\n"+'Checkpoint includes aligned model/AdamW/Torch RNG/private Python RNG. Raw old/new JSON retains every generated token and unedited character. Semantic/full-language judgment is pending actual complete reading; no score or gate pass is guessed. No public model/site replacement or TEST generation. No new TEST data acquisition or model evaluation.\n')
for raw in [R/'continue-10000/checkpoint.pt',R/'continue-10000/checkpoint-0.pt',R/'continue-10000/best-aligned-checkpoint.pt']:
 if raw.exists():pack(raw)
files=[str(p.relative_to(REPO)) for p in R.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ['automatic-publish.log','automatic-publish-complete.json','checkpoint.pt','checkpoint-0.pt','best-aligned-checkpoint.pt','.training.lock','.controller.lock','train.tokens.bin'] and not p.name.endswith('.tmp')]
run(['git','add','--',*files]);run(['git','commit','-m',f'Save Round37 actual retained {step} updates and ungraded mechanical evidence']);commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip();run(['git','-c','pack.threads=1','push'])
pr=json.loads(subprocess.check_output(['gh','pr','view','--json','number'],cwd=REPO,text=True))['number']
body=f"Round37: ONLY original newline main CE excluded at eligible human EOS positions; coefficient0.3 fixed; paired same R28 initial state and10000 dose as R36; same data, model, optimizer, LR, sampling masses and64-token negative horizon; same adopted teacherUL1.0 plus sequenceUL0.1every10, model, LR and aligned Round28 parent; paired comparator Round36; adoption anchor remains Round25. Actual retained updates {step}/10000; optimizer counters {counters}; best exposed-DEV NLL {record['bestDevelopmentNllPerByte']}; selected step {record['selectedStep']}; pipeline exit {status}. Weights/optimizer/RNG and full raw traces saved at {commit}. Full semantic reading pending, no score guessed, no new TEST or public replacement. See training/language/round37/MECHANICAL_STATUS.md."
run(['gh','api',f'repos/4k29/4k29/pulls/{pr}','--method','PATCH','--input','-'],input=json.dumps({'body':body}).encode(),stdout=subprocess.DEVNULL)
write(E/'automatic-publish-complete.json',dict(commit=commit,pr=pr,actualRetainedAdditionalUpdates=step,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),languageReviewPending=True));print(json.dumps({'actualRetainedAdditionalUpdates':step,'savedCommit':commit,'pr':pr}),flush=True)
