from pathlib import Path
import json
R=Path('/workspace/4k29/training/language/round46');E=R/'execution';P=R.parent/'round45'
# No core changes: inherited initialization description is preserved byte-for-byte but explicitly corrected in metadata.
(E/'initialization-description-erratum.json').write_text(json.dumps(dict(actualUpdates=0,inheritedDescription='hold terminal learning rate',actualBehavior='Frozen train.py overrides all loaded optimizer param-group LR using CLI --lr before any update',learningRate=4.4999999999999996e-5,scientificControl='round44',allOtherOptimizerGroupsMomentsAndRngMustMatch=True,coreLearningCodeUnchanged=True),indent=2)+'\n')
f=E/'execute.py';s=f.read_text().replace("'--lr','2.2499999999999998e-05'","'--lr',str(json.loads((ROOT/'policy.json').read_text())['learningRate'])");f.write_text(s)
for name,left,right in [('verify_initial.py','a','b'),('paired_training_audit.py','zb','za')]:
 f=E/name;s=f.read_text();line=f"assert {left}['optimizer']['param_groups']=={right}['optimizer']['param_groups']"
 repl=f"""groups_left=[dict(g) for g in {left}['optimizer']['param_groups']];groups_right=[dict(g) for g in {right}['optimizer']['param_groups']]
assert len(groups_left)==len(groups_right)
for gl,gr in zip(groups_left,groups_right):
 assert gl['lr']==4.4999999999999996e-5 and gr['lr']==2.2499999999999998e-5
 gl['lr']=gr['lr']
assert groups_left==groups_right"""
 s=s.replace(line,repl) if line in s else s.replace(f"assert {right}['optimizer']['param_groups']=={left}['optimizer']['param_groups']",repl).replace('initialAdamWMomentsAndGroupsExactlyEqual=True','initialAdamWMomentsAndOtherGroupsExactlyEqual=True,onlyParamGroupLearningRateDiffers=True').replace('sameAlignedInitialModelOptimizerAndRng=True','sameAlignedInitialModelMomentsAndRngExceptDeclaredLearningRate=True');f.write_text(s)
f=E/'verify_single_condition.py';s=(P/'execution/verify_single_condition.py').read_text().replace("P=R.parent/'round44'","P=R.parent/'round44'").replace('round45/','round46/');s=s.replace("assert a['contextPreference']['coefficient']==.1 and b['contextPreference']['coefficient']==.2","assert a['learningRate']==2.2499999999999998e-5 and b['learningRate']==4.4999999999999996e-5;assert a['contextPreference']['coefficient']==b['contextPreference']['coefficient']==.1").replace("y['contextPreference']['coefficient']=.1","y['learningRate']=a['learningRate']").replace('contextPreference.coefficient0.1 to0.2','learningRate2.2499999999999998e-5 to4.4999999999999996e-5');f.write_text(s)
f=E/'publish_mechanical.py';s=f.read_text();a=s.index('Round46: ONLY');b=s.index('Actual retained updates',a);s=s[:a]+'Round46: ONLY double fixed learning rate2.2499999999999998e-5 to4.4999999999999996e-5 against R44; retain coefficient0.1, main RealPersona40%, JMRD5%, unchanged data/model/all other objectives/RNG/10000 dose. R45 coefficient0.2 is rejected and is not the scientific control. Same optimizer-aligned Round28 parent; adoption anchor remains Round25. '+s[b:];f.write_text(s)
# Refresh bootstrap source: final preparation fixes are preserved beside it before input freeze.
import shutil
shutil.copy2(__file__,E/'fix_trial_metadata.py')
p=json.loads((R/'policy.json').read_text());assert p['learningRate']==4.4999999999999996e-5 and p['contextPreference']['coefficient']==.1
(R/'README.md').write_text('# R46 — R44に対して学習率だけ2倍\n\n実更新0、開始前監査中。R44の係数0.1・主sampling40%+5%・全10core files・資料・pool1024・他loss・model・seed・R28fullstate・10000dose・selector・gateを維持し、LRだけ2.2499999999999998e-5から4.4999999999999996e-5へ変更。R45は不採用の失敗参照であり科学対照ではない。公開/R25anchor維持。\n')
print('R46 metadata, single LR condition and optimizer-group exception corrected before freeze; actual0')
