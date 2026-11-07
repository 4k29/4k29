from pathlib import Path
import json
R=Path('/workspace/4k29/training/language/round46');E=R/'execution';P=R.parent/'round44'
# Frozen computational trainer loads original groups and writes CP0 before overriding LR inside each update.
for name in ['verify_initial.py','paired_training_audit.py']:
 f=E/name;s=f.read_text();a=s.index('groups_left=');b=s.index('\nfor ',s.index('assert groups_left==groups_right',a))
 replacement="assert a['optimizer']['param_groups']==b['optimizer']['param_groups']" if name=='verify_initial.py' else "assert za['optimizer']['param_groups']==zb['optimizer']['param_groups']"
 s=s[:a]+replacement+s[b:]
 s=s.replace('initialAdamWMomentsAndOtherGroupsExactlyEqual=True,onlyParamGroupLearningRateDiffers=True','initialAdamWMomentsAndGroupsExactlyEqualAtZero=True,learningRateOverriddenOnlyImmediatelyBeforeEachActualUpdate=True').replace('sameAlignedInitialModelMomentsAndRngExceptDeclaredLearningRate=True','sameAlignedInitialModelOptimizerAndRngAtZero=True,learningRateDiffersOnlyForActualUpdates=True')
 f.write_text(s)
(E/'initialization-description-erratum.json').write_text(json.dumps(dict(actualUpdates=0,inheritedDescription='hold terminal learning rate',actualBehavior='CP0 retains exact parent optimizer groups. Frozen train.py overrides every param-group LR inside each actual update before forward/backward/step, starting at update1. No core code changes.',zeroCheckpointLearningRate=2.2499999999999998e-5,actualUpdateLearningRate=4.4999999999999996e-5,scientificControl='round44',allInitialOptimizerGroupsMomentsAndRngExactlyMatch=True,allOtherUpdateGroupsMustMatch=True,correctsProspectiveR45NextNoteAboutZeroLr=True),indent=2)+'\n')
# Restore execution-copy helper consistency to reflect actual zero-state behavior.
(E/'fix_trial_metadata.py').write_text(Path('/workspace/fix_round46_preflight.py').read_text())
(E/'correct_lr_timing.py').write_text(Path(__file__).read_text())
print('Exact CP0 group equality retained; 2x LR applied at every real update by unchanged trainer')
