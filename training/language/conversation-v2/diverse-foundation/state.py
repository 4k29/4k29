from common import *
def starting(arm):
 base=initial()['trajectory'];before=digest(base)
 if arm=='A':model,_,rng=restore_isolated(base)
 else:
  torch.manual_seed(41029);model=decoder(base['config']);rng=random.Random();rng.setstate(base['pythonRng'])
 opt=torch.optim.AdamW(model.parameters(),lr=2e-4,betas=(.9,.999),eps=1e-8,weight_decay=.05)
 torch.set_rng_state(base['torchRng']);model.train();assert digest(base)==before
 return model,opt,rng,base

def rate(step,plan):
 lr=plan['lr'];w=lr['warmup'];n=plan['full_pass_updates'];assert 1<=step<=n
 return lr['peak']*step/w if step<=w else lr['end']+(lr['peak']-lr['end'])*.5*(1+math.cos(math.pi*(step-w)/(n-w)))
