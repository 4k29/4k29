"""Post-selection bounded TRAIN/development gap; no selection, TEST or optimizer."""
import pathlib,sys,random,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from train import load_partition,pack,Decoder,torch,F,read,write,sha
DATA=ROOT.parent/'round11/multiview';torch.set_num_threads(2)
partitions={f:load_partition(DATA,f) for f in ['train','validation']};rng=random.Random(3132)
sites=sorted(set(r['site'] for r in partitions['train'][0]['rows'])&set(r['site'] for r in partitions['validation'][0]['rows']));selected={f:{} for f in partitions}
for site in sites:
 pools={f:[r for r in i['rows'] if r['site']==site and r['variant']==0] for f,(i,v) in partitions.items()};n=min(32,*(len(v) for v in pools.values()))
 for f in partitions:selected[f][site]=rng.sample(pools[f],n)
assert not ({r['document'] for rows in selected['train'].values() for r in rows}&{r['document'] for rows in selected['validation'].values() for r in rows})
byte_lengths=torch.tensor([len(bytes.fromhex(b)) for b in read(DATA/'tokenizer.json')['bytes']])
models={};paths={'parentRound10':ROOT.parent/'round10/word-512-continue-10000/checkpoint.pt','round11':ROOT.parent/'round11/continue-10000/checkpoint.pt','round12':ROOT/'continue-10000/checkpoint.pt'}
for name,path in paths.items():
 cp=torch.load(path,map_location='cpu',weights_only=False);model=Decoder(cp['config']);model.load_state_dict(cp['beststate']);model.eval();folds={}
 for f,(info,values) in partitions.items():
  loss=tokens=bytes_seen=0;by_site={}
  for site,rows in selected[f].items():
   total=count=bytecount=0
   for start in range(0,len(rows),8):
    x,y=pack(rows[start:start+8],values,256)
    with torch.no_grad():total+=float(F.cross_entropy(model(x).reshape(-1,cp['config']['vocabulary']),y.reshape(-1),reduction='sum'))
    targets=y[y!=-100];count+=len(targets);bytecount+=int(byte_lengths[targets].sum())
   by_site[site]=dict(rows=len(rows),targets=count,utf8Bytes=bytecount,tokenLoss=total/count,nllPerUtf8Byte=total/bytecount);loss+=total;tokens+=count;bytes_seen+=bytecount
  genres={'aozora':.45,'mic':.1,'env':.1,'mdn':.15,'jma':.1,'maff':.025,'stat':.05,'bunka':.025};mass=sum(genres[s] for s in sites)
  folds[f]=dict(rows=sum(len(r) for r in selected[f].values()),targets=tokens,utf8Bytes=bytes_seen,pooledTokenLoss=loss/tokens,pooledNllPerUtf8Byte=loss/bytes_seen,genreWeightedNllPerUtf8Byte=sum(genres[s]/mass*d['nllPerUtf8Byte'] for s,d in by_site.items()),sites=by_site)
 models[name]=dict(checkpointSha256=sha(path),selectedStep=cp['beststep'],folds=folds,developmentMinusTrainNllPerByte=folds['validation']['genreWeightedNllPerUtf8Byte']-folds['train']['genreWeightedNllPerUtf8Byte'])
record=dict(seed=3132,canonicalOnly=True,rawSelectedFp32=True,additionalOptimizerUpdates=0,selectionUsedDiagnostic=False,testRead=False,sharedSourceDocumentIds=False,maxRowsPerSitePerFold=32,models=models,selectedRows=selected,sourceIndexSha256={f:sha(DATA/f'{f}.index.json') for f in partitions},limitations='Posthoc finite site-stratified row sample, not full TRAIN loss. Same selected rows for all models; unequal row lengths/context prefixes and existing short text overlaps remain. Positive gap alone does not prove overfitting, data bias or capacity causation.')
write(ROOT/'execution/train-development-gap.json',record);print(json.dumps({n:dict(train=d['folds']['train']['genreWeightedNllPerUtf8Byte'],development=d['folds']['validation']['genreWeightedNllPerUtf8Byte'],gap=d['developmentMinusTrainNllPerByte']) for n,d in models.items()}))
