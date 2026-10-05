"""Own randomly initialized decoder: no pretrained layers or outside weights.
PyTorch provides numerical operators and automatic differentiation only.
"""
import math
import torch
from torch import nn
from torch.nn import functional as F

class Block(nn.Module):
    def __init__(self,dim,heads,hidden,dropout):
        super().__init__();self.heads=heads
        self.ln1=nn.LayerNorm(dim);self.qkv=nn.Linear(dim,dim*3);self.proj=nn.Linear(dim,dim)
        self.ln2=nn.LayerNorm(dim);self.fc1=nn.Linear(dim,hidden);self.fc2=nn.Linear(hidden,dim);self.dropout=nn.Dropout(dropout)
    def forward(self,x):
        batch,steps,dim=x.shape
        q,k,v=self.qkv(self.ln1(x)).chunk(3,dim=-1)
        q,k,v=[a.view(batch,steps,self.heads,dim//self.heads).transpose(1,2) for a in (q,k,v)]
        # Fused causal matrix/softmax numerical operation; architecture/weights are ours.
        attention=F.scaled_dot_product_attention(q,k,v,is_causal=True,dropout_p=0).transpose(1,2).contiguous().view(batch,steps,dim)
        x=x+self.dropout(self.proj(attention))
        return x+self.dropout(self.fc2(F.gelu(self.fc1(self.ln2(x)),approximate='tanh')))
class Decoder(nn.Module):
    def __init__(self,config):
        super().__init__();self.config=config
        self.token=nn.Embedding(config['vocabulary'],config['dim']);self.position=nn.Embedding(config['context'],config['dim'])
        self.blocks=nn.ModuleList([Block(config['dim'],config['heads'],config['hidden'],config['dropout']) for _ in range(config['layers'])]);self.norm=nn.LayerNorm(config['dim']);self.apply(self.initialize)
    @staticmethod
    def initialize(module):
        if isinstance(module,(nn.Embedding,nn.Linear)):nn.init.normal_(module.weight,mean=0,std=.02)
        if isinstance(module,nn.Linear):nn.init.zeros_(module.bias)
    def forward(self,tokens):
        x=self.token(tokens)+self.position(torch.arange(tokens.shape[1],device=tokens.device))
        for block in self.blocks:x=block(x)
        return F.linear(self.norm(x),self.token.weight)
