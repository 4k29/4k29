"""Independent schedule/window/ending/dose check, no model or optimizer created."""
import argparse,collections,gzip,hashlib,json,pathlib,sys
import numpy as np
HERE=pathlib.Path(__file__).resolve().parent;BASE=HERE.parents[1]
sys.path.insert(0,str(BASE));from core import open_tokens,pack
from schedule_batches import sequences_for_step,pack_sequences
def read(p):return json.loads(pathlib.Path(p).read_text())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main(folder,out):
    r=read(folder/'receipt.json');index=read(folder/'native-window-index.json');values=np.memmap(folder/'native-selected-windows.u32',dtype='<u4',mode='r')
    if sha(folder/'native-selected-windows.u32')!=r['nativeWindowBinarySha256']or sha(folder/'schedule.jsonl.gz')!=r['scheduleSha256']:raise ValueError('Frozen schedule input changed')
    data=read(BASE/'data/data.json');rp_values,rp_windows=open_tokens(data,'train');vocabulary=len(read(BASE/'data/tokenizer.json')['bytes'])
    common=[];replacement=[];native_positions=[];target_sum=0;endings=0;kind_counts={'control':collections.Counter(),'dataadd':collections.Counter()};padding=0
    with gzip.open(folder/'schedule.jsonl.gz','rt')as f:
        rows=[json.loads(line)for line in f]
    if len(rows)!=2048 or len(index)!=4096:raise ValueError('Missing planned windows/steps')
    for expected,row in enumerate(rows,1):
        if row['step']!=expected:raise ValueError('Step order gap')
        control,treatment=sequences_for_step(row,rp_values,rp_windows,values,index)
        if control[:2]!=treatment[:2]:raise AssertionError('Common RP windows changed')
        for name,seqs in [('control',control),('dataadd',treatment)]:
            for seq in seqs:
                if any(t in (0,5)or t>=vocabulary for t in seq):raise ValueError('PAD/reserved token entered source data')
                target=seq[1:];kind_counts[name].update(dict(targets=len(target),body=sum(t>=6 for t in target),eos=target.count(2),role=sum(t in(3,4)for t in target),other=target.count(1)))
        common.extend(row['sharedRpWindowIndices']);replacement.extend(row['controlReplacementRpWindowIndices']);native_positions.extend(row['treatmentNativeWindowPositions']);target_sum+=row['activeTargetCountBoth'];padding+=1024-row['activeTargetCountBoth']
        # Check actual unchanged core.pack on fixed representatives, including
        # the smallest active batch and a native true-end partial case.
    probes=sorted({0,min(range(len(rows)),key=lambda i:rows[i]['activeTargetCountBoth']),next(i for i,row in enumerate(rows)if any(index[j]['trueDocumentEnd']for j in row['treatmentNativeWindowPositions']))})
    for i in probes:
        control,treatment=sequences_for_step(rows[i],rp_values,rp_windows,values,index)
        packs=[pack_sequences(seqs,vocabulary,pack)for seqs in [control,treatment]]
        if any(int((y!=-100).sum())!=rows[i]['activeTargetCountBoth']for x,y,s in packs):raise AssertionError('core.pack lost or invented active targets')
        if not(packs[0][1]!=-100).equal(packs[1][1]!=-100):raise AssertionError('Paired PAD masks differ')
    if len(set(common+replacement))!=8192 or set(native_positions)!=set(range(4096)):raise AssertionError('Window replacement repeated/skipped')
    native_ends=collections.Counter()
    for w in index:
        seq=values[w['tokenFileOffset']:w['tokenFileOffset']+w['length']]
        if 2 in seq:
            if seq[-1]!=2 or not w['trueDocumentEnd']or w['offset']+w['length']!=w['documentTokenCount']:raise AssertionError('Fake native EOS')
            native_ends[w['source']]+=1
    if dict(native_ends)!=r['selectedNativeTrueEnds']or kind_counts['control']!=r['controlDose']or kind_counts['dataadd']!=r['treatmentDose']:raise AssertionError('Dose report differs from actual tokens')
    if target_sum!=r['controlDose']['targets']or padding!=r['paddingTargetPositionsIgnoredPerArm']:raise AssertionError('Token/padding budget changed')
    result=dict(passed=True,actualStepsAudited=2048,perArmGenuineTargetTokens=target_sum,perArmIgnoredPaddingPositions=padding,
        perStepAndSlotActiveLengthsMatched=True,sharedRpSourcesIdentical=True,all8192ControlWindowsDistinct=True,
        native4096WindowsExactlyOnce=True,nativeTrueEndings=dict(native_ends),allDoseCountsRecomputedFromActualTokenIds=True,
        originalCorePackWithPartialTargetsPass=True,corePackRepresentativeSteps=[rows[i]['step']for i in probes],
        bodyEosRoleDoseNotClaimedEqual=True,candidateDataAdmission=False,modelObjectsCreated=0,optimizerUpdates=0,sealedTestRead=False,
        scheduleSha256=r['scheduleSha256'],nativeWindowBinarySha256=r['nativeWindowBinarySha256'])
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();main(a.folder,a.output)
