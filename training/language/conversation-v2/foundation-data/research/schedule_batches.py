"""Materialize the planned source replacement with the existing PAD/CE contract."""
import numpy as np
def sequences_for_step(row,rp_values,rp_windows,native_values,native_index):
    def rp(i):
        w=rp_windows[i];return np.array(rp_values[w['offset']:w['offset']+w['length']],dtype=np.int64).tolist()
    def native(i):
        w=native_index[i]
        if w['partition']!='train':raise ValueError('Native non-TRAIN window in learner schedule')
        values=np.array(native_values[w['tokenFileOffset']:w['tokenFileOffset']+w['length']],dtype=np.int64).tolist()
        if w['trueDocumentEnd']!=(values[-1]==2):raise ValueError('Native ending changed')
        if 2 in values and (values.count(2)!=1 or w['offset']+w['length']!=w['documentTokenCount']):raise ValueError('Fake or repeated native document EOS')
        if 1 in values and not(w['offset']==0 and values[0]==1 and values.count(1)==1):raise ValueError('Fake native document BOS')
        return values
    shared=[rp(i)for i in row['sharedRpWindowIndices']]
    control=shared+[rp(i)for i in row['controlReplacementRpWindowIndices']]
    treatment=shared+[native(i)for i in row['treatmentNativeWindowPositions']]
    if [len(x)for x in control]!=[len(x)for x in treatment]:raise ValueError('Per-slot active lengths differ')
    if sum(len(x)-1 for x in control)!=row['activeTargetCountBoth']:raise ValueError('Frozen target budget changed')
    return control,treatment

def pack_sequences(sequences,vocabulary,pack_function):
    values=[];windows=[]
    for seq in sequences:
        if not 2<=len(seq)<=257:raise ValueError('Wrong actual source window length')
        windows.append(dict(offset=len(values),length=len(seq)));values.extend(seq)
    return pack_function(np.asarray(values,dtype=np.uint32),windows,list(range(len(windows))),vocabulary)
