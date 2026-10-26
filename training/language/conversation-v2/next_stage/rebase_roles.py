"""Future human-A/B prefix contract. NOT used in the frozen current pilot.

These are interchangeable human identities, not semantic user/AI roles.
Do not apply this mapping to an assistant instruction prompt.
"""
def rebase_human_prefix(prefix):
    if len(prefix)<4 or prefix[0]!=1 or prefix[1] not in (3,4) or prefix[-1] not in (3,4):
        raise ValueError('Need BOS, complete human turns and final response role')
    i=1;previous=None
    while i<len(prefix)-1:
        role=prefix[i]
        if role not in (3,4) or role==previous:raise ValueError('Human source roles must alternate')
        previous=role;i+=1
        while i<len(prefix)-1 and prefix[i]>=6:i+=1
        if i>=len(prefix)-1 or prefix[i]!=2:raise ValueError('Complete real utterance EOS required')
        i+=1
    if i!=len(prefix)-1 or prefix[-1]==previous:raise ValueError('Response speaker must differ')
    swap=prefix[1]==4
    out=[7-t if swap and t in (3,4) else t for t in prefix]
    assert out[1]==3 and [t for t in out if t>=6]==[t for t in prefix if t>=6]
    assert out.count(2)==prefix.count(2)
    return out,{'speakerIdMapping':{'3':4,'4':3} if swap else {'3':3,'4':4},
                'currentPilotUsed':False,'ordinaryTokenOrEosModified':False}
