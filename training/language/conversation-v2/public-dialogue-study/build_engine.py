import pathlib
P=pathlib.Path(__file__).parent;s=(P/'engine-original.py').read_text()
s=s.replace('Four one-pass updates/arm','Seventeen one-pass updates/arm').replace('scratch-response-learning','scratch-public-dialogue')
s=s.replace("list(range(4))","list(range(data['updates_per_arm']))").replace("P/'PILOT_DATA.json'","P/'DATA.json'")
s=s.replace('HEAD:research/response-learning-pilot','HEAD:research/public-dialogue-ce-study')
s=s.replace("data=read(P/'DATA.json');plan=read(P/'PLAN.json')","data=read(P/'DATA.json');data['pilot_train']=data['parts']['train'];data['dev']=data['parts']['dev'];plan=read(P/'PLAN.json')")
s=s.replace("panel='human-dev19'","panel='ASDC-condition-dev15'")
s=s.replace("for i in range(4):","for i in range(data['updates_per_arm']):").replace("if i+1 in [2,4]:","if i+1 in [9,17]:").replace("if i==1:\n     del m,o,r","evaluate(obj,arm+'-pilot'+str(i+1),i+1==17)\n    if i==8:\n     del m,o,r")
s=s.replace("  evaluate(obj,arm+'-pilot4',True);assert digest(src)==original;publish(f'Save {arm} four-update pilot raw evaluation');del m,o,r,obj","  assert digest(src)==original;publish(f'Save {arm} seventeen-update pilot raw evaluation');del m,o,r,obj")
s=s.replace("actual_optimizer_returns=14,intents=14,retained=8","actual_optimizer_returns=40,intents=40,retained=34").replace("Complete14 actual optimizer calls","Complete40 actual optimizer calls")
# Atomic runtime save is inherited. Refuse ambiguous repeated execution; write hardware evidence first.
s=s.replace("write(P/'SOURCE_STATE.json'", "write(P/'RESOURCE.json',dict(disk=__import__('shutil').disk_usage(W)._asdict(),CPU=os.cpu_count(),threads=torch.get_num_threads(),RAM_meminfo=pathlib.Path('/proc/meminfo').read_text(),GPU_available=torch.cuda.is_available(),run_id=os.environ.get('GITHUB_RUN_ID')));write(P/'SOURCE_STATE.json'")
(P/'engine.py').write_text(s)
compile(s,'engine.py','exec');print('engine compiled')
