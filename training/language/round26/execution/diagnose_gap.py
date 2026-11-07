"""New selected model on cached exact TRAIN/development rows; zero updates."""
import pathlib,sys,json
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from train import read,write,sha,torch,Decoder,load_partition,pack,F
BASE=ROOT.parent/'round12/execution/train-development-gap.json';old=read(BASE);DATA=ROOT.parent/'round11/multiview';torch.set_num_threads(2)
assert old['canonicalOnly'] and old['additionalOptimizerUpdates']==0 and not old['testRead']
for f,h in old['sourceIndexSha256'].items():assert sha(DATA/f'{f}.index.json')==h
path=ROOT/'continue-10000/checkpoint.pt';cp=torch.load(path,map_location='cpu',weights_only=False);assert cp['step']==10000
model=Decoder(cp['config']);model.load_state_dict(cp['beststate']);model.eval();byte_lengths=torch.tensor([len(bytes.fromhex(b)) for b in read(DATA/'tokenizer.json')['bytes']]);folds={}
genres={'aozora':.45,'mic':.1,'env':.1,'mdn':.15,'jma':.1,'maff':.025,'stat':.05,'bunka':.025}
for f,by_site in old['selectedRows'].items():
 info,values=load_partition(DATA,f);loss=tokens=bytes_seen=0;sites={}
 for site,rows in by_site.items():
  total=count=bytecount=0
  for start in range(0,len(rows),8):
   x,y=pack(rows[start:start+8],values,256)
   with torch.no_grad():total+=float(F.cross_entropy(model(x).reshape(-1,cp['config']['vocabulary']),y.reshape(-1),reduction='sum'))
   targets=y[y!=-100];count+=len(targets);bytecount+=int(byte_lengths[targets].sum())
  sites[site]=dict(rows=len(rows),targets=count,utf8Bytes=bytecount,tokenLoss=total/count,nllPerUtf8Byte=total/bytecount);loss+=total;tokens+=count;bytes_seen+=bytecount
 mass=sum(genres[s] for s in sites);folds[f]=dict(rows=sum(d['rows'] for d in sites.values()),targets=tokens,utf8Bytes=bytes_seen,pooledTokenLoss=loss/tokens,pooledNllPerUtf8Byte=loss/bytes_seen,genreWeightedNllPerUtf8Byte=sum(genres[s]/mass*d['nllPerUtf8Byte'] for s,d in sites.items()),sites=sites)
record={k:v for k,v in old.items() if k!='models'};record['models']={k:old['models'][k] for k in ['parentRound10','round11']};record['models'][ROOT.name]=dict(checkpointSha256=sha(path),selectedStep=cp['beststep'],folds=folds,developmentMinusTrainNllPerByte=folds['validation']['genreWeightedNllPerUtf8Byte']-folds['train']['genreWeightedNllPerUtf8Byte']);record['baselineCacheSha256']=sha(BASE);record['baselineMeasurementsReusedAfterInputIdentityCheck']=True;record['trainingRowsDiagnosticScope']='Fixed old TRAIN canonical rows only; excludes recovered Round19 MAFF and new Round22 JMA/MAFF prose and Round26 wiki2019 corpus. Not whole expanded TRAIN generalization.'
write(ROOT/'execution/train-development-gap.json',record);print(json.dumps({n:dict(train=d['folds']['train']['genreWeightedNllPerUtf8Byte'],development=d['folds']['validation']['genreWeightedNllPerUtf8Byte'],gap=d['developmentMinusTrainNllPerByte']) for n,d in record['models'].items()}))
