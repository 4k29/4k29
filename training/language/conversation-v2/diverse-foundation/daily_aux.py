"""Ordinary daily prose side panel: AI-authored prompts, no targets/training, no adoption gate changes."""
import argparse
from common import *
from evaluate import load
from prose_decode import greedy

def main():
 a=argparse.ArgumentParser();a.add_argument('--freeze',action='store_true');a.add_argument('--model');args=a.parse_args();path=D/'DAILY_PROSE_PROTOCOL.json'
 if args.freeze:
  prompts=['朝、窓を開けると、涼しい風が入ってきました。私は','料理を始める前に、まず','友達と旅行の予定を相談しています。行き先はまだ決まっていませんが、','雨が降り始めたので、','買い物に行く前に、冷蔵庫の中を確認しました。足りないものは','読みかけの本が面白くて、','夕食の片付けが終わったら、','明日は休みです。ゆっくり過ごしたいので、'];enc=Encoder(read(V/'data/tokenizer.json'));write(path,dict(cases=[dict(id=f'daily-prose-{i}',panel='assistant-authored-daily-prose',prompt=p,prefix=[1]+enc(p))for i,p in enumerate(prompts)],authorship='main assistant-authored diagnostic prompts, not independent human original or TEST',reference='No generated answer targets; evaluate arbitrary appropriate natural continuation, not exact match',generation='full-vocabulary greedy128, original EOS2, no repair or penalties',registered_after_common_before_terminal=True,role='Auxiliary to check specialist-prose benchmark bias; never alters primary old24/new9/JMA12 gates or original selection',optimizer_updates=0));return
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);model,cur=load(args.model);model.eval();p=read(path);pieces=[bytes.fromhex(t)for t in read(V/'data/tokenizer.json')['bytes']];out=D/'daily-prose';out.mkdir(exist_ok=True);assert not(out/(args.model+'.json')).exists()
 with torch.inference_mode():cases=[{**c,**greedy(model,c['prefix'],pieces,max_new=128)}for c in p['cases']]
 write(out/(args.model+'.json'),dict(model=args.model,cursor=cur,cases=cases,protocol_sha256=sha(path),primary_gate=False,independent_native_human=False,optimizer_updates=0))
if __name__=='__main__':main()
