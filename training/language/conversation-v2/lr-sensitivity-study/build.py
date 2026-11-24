"""Only inherited LF projection; never collect/resample/rebuild training data."""
def collapse(t):
 keep=[i for i,v in enumerate(t) if not(v==16 and i and t[i-1]==16)]
 return [t[i] for i in keep],keep
