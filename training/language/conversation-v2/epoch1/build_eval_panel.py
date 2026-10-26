"""Freeze source-authored content-required DEV; never inspect model outputs."""
import hashlib,json,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent;BASE=HERE.parent
sys.path.insert(0,str(BASE));sys.path.insert(0,str(BASE/'next_stage'))
from core import sha
from new_tokenizer import Encoder
from rebase_roles import rebase_human_prefix

def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
# Original-source manual selection, independent of generated outputs. Exact references
# are illustrative human continuations, never the only acceptable model answer.
SELECTION=[('01588',4,'question-answer','弁当の中身を具体的に答える'),('02143',3,'question-answer','好きな芸人または好みの有無を具体的に答える'),('03127',3,'question-answer','スポーツをするか、見るかを答える'),('00398',4,'context-reference','仕事をしているか、就業状況に答える'),('12131',13,'question-answer','カフェで何をするか答える'),('10825',22,'question-answer','翌日の具体的な予定または未定を答える'),('03128',19,'explanation','番組の内容や知っている範囲を述べる'),('03395',17,'explanation','直前で指定した作品の筋や設定を説明する'),('10823',8,'context-reference','洗濯物を外か室内かどこに干すか答える'),('10163',8,'question-answer','滞在期間を答える'),('02234',8,'question-answer','他に見ているドラマを答える'),('10213',5,'context-reference','秋の外出や予定について具体的に答える'),('12318',3,'question-answer','最近の外食の有無や料理を答える'),('10587',8,'context-reference','エアコンを使うか代わりに何を使うか答える'),('13655',7,'explanation','作品を面白いと思う理由または意見を述べる'),('12316',11,'explanation','経営に関する作品内の出来事を説明する'),('09758',19,'context-reference','名探偵コナンのどちらを指したのか明確にする'),('00186',8,'question-answer','自分の予定を具体的に答える'),('05544',3,'question-answer','趣味を具体的に答える'),('12268',5,'recommendation','テレビや漫画の具体的な推薦または理由ある不推薦を返す'),('05998',6,'context-reference','直前の食べ物の話題に沿って好みを具体的に答える'),('04863',22,'explanation','動物の性別や性格の違いについて答える'),('04632',17,'explanation','月曜日に作る理由を説明する'),('13649',17,'explanation','仕事で大変な点や納期について説明する')]

def main():
 tok=json.loads((BASE/'data/tokenizer.json').read_text());encode=Encoder(tok)
 docs={d['id']:d for d in map(json.loads,(BASE/'data/dev.docs.jsonl').read_text().splitlines())}
 old=json.loads((BASE/'data/benchmark-dev.json').read_text())['cases'];oldids={c['document']for c in old};new=[]
 for j,(n,i,category,requirement)in enumerate(SELECTION):
  d=docs['realpersona:'+n];assert d['id']not in oldids
  u=d['utterances'][i];h=d['utterances'][i-2:i];prefix=[1]
  for x in h:prefix += [x['localRoleToken']]+encode(x['text'])+[2]
  prefix += [u['localRoleToken']];unified,mapping=rebase_human_prefix(prefix);gold=encode(u['text'])
  assert len(prefix)<=64 and len(gold)<=96 and len(prefix)+192<=256
  new.append(dict(id=f'v2-content-dev-{j:03d}',document=d['id'],split='additional-DEV-only-never-TEST',sourceSha256=d['sourceSha256'],sourceUrl=d['sourceUrl'],license=d['license'],attribution=d['attribution'],prefixTokens=unified,originalPrefixTokens=prefix,roleMapping=mapping,goldTokens=gold,goldEos=2,targetText=u['text'],targetOrdinal=i,history=h,historyTurns=2,targetLocalRoleToken=unified[-1],prefixText='\n'.join(x['text']for x in h)+'\n',category=category,contentRequired=True,minimumSemanticRequirement=requirement,referenceIsNotUniqueAcceptableReply=True,newTokenizerTrainExposure=False,R46TrainExposure=True,generationMaxNewTokens=192))
 assert len({c['document']for c in new})==24
 frozen=dict(status='Frozen before endpoint inference; manually source-selected development probes',cases=new,sourceSha256=sha(BASE/'data/dev.docs.jsonl'),tokenizerSha256=sha(BASE/'data/tokenizer.json'),modelOutputSeenDuringSelection=False,sealedTestUsed=False,noSyntheticAnswerTargets=True,limitations=['All are original human-human continuations, not AI role instruction positives','Selection favors contentful human gold and explicit questions; not a balanced population estimate','Personal facts are human-role continuation examples, not truths about an AI','Advice and conditional instruction coverage remain absent; require future separately authored human benchmark','Same source and small speaker population; not source-independent TEST'])
 write(HERE/'content-dev.json',frozen)
 unifiedold=[]
 for c in old:
  q=dict(c);q['originalPrefixTokens']=c['prefixTokens'];q['prefixTokens'],q['roleMapping']=rebase_human_prefix(c['prefixTokens']);q['targetLocalRoleToken']=q['prefixTokens'][-1];unifiedold.append(q)
 write(HERE/'unified32-dev.json',dict(cases=unifiedold,sourceBenchmarkSha256=sha(BASE/'data/benchmark-dev.json'),contract='Every BOS evaluation history starts local human-A3, bijective swap3/4 across history and response; body/EOS/source speaker identities unchanged',sealedTestUsed=False))
 report=dict(passed=True,originalCases=32,swappedCases=sum(c['roleMapping']['speakerIdMapping']['3']==4 for c in unifiedold),unifiedStartRole3=all(c['prefixTokens'][:2]==[1,3]for c in unifiedold+new),unchangedBodyAndEos=all([t for t in c['originalPrefixTokens']if t not in(3,4)]==[t for t in c['prefixTokens']if t not in(3,4)]for c in unifiedold+new),newContentRequiredCases=24,newUniqueDocuments=24,overlapOldDocuments=0,allGenerationFits256=True,trainOriginalDocumentStart='already BOS1 role3; no corpus/tokenizer/training-window change',devWindowContract='64 original packed DEV windows unchanged; fragments never gain artificial BOS/role',actualOptimizerUpdates=0,inferenceCalls=0)
 write(HERE/'input-contract-preflight.json',report)
 rubric=dict(frozenBeforeInference=True,dimensions=['grammaticalNaturalWhole','semanticAppropriateWhole','specificContentAppropriate','contextConsistent','harmfulRepetition','topicDrift','naturalTermination'],contentSuccess='Must satisfy case-specific semantic requirement with meaningful information; acknowledgement, merely repeating question, or unrelated natural short text fails.',fullSuccess='All whole-text grammar, relevance, context, meaningful content and appropriate actual EOS; no harmful repetition or drift.',noNllOnlySuccess=True,noExactGoldRequirement=True,independentReview='Blind endpoint identifiers before whole-text reading; preserve uncertainty and disagreements; assistants are not independent native human raters',newDevThreshold='Research signal only: >=4 additional content-success cases of24 vs same-model512 with no harmful repetition increase; does not constitute formal adoption or Phase1 pass',oldStrictGates='17/13/9, Pareto and repetition conditions unchanged, not replaced by this panel',noPostOutputCheckpointSelection=True)
 write(HERE/'EVALUATION_RUBRIC.json',rubric)
 print(json.dumps(report))
if __name__=='__main__':main()
