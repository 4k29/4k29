"""Group padding widths; preserve each original row's sampling probability."""
import collections

WIDTHS=(64,128,256)
VIEWS={0:.4,1:.3,2:.3}

def sampler(rows,genres):
    source=lambda r: ('jmrd' if r['document'].startswith('jmrd:') else 'realpersona') if r['site']=='human-chat' else 'other'
    counts=collections.Counter((r['site'],r['variant'],source(r)) for r in rows)
    strata=collections.defaultdict(list)
    for r in rows:
        width=next(w for w in WIDTHS if r['length']-1<=w)
        strata[(r['site'],r['variant'],width,source(r))].append(r)
    source_masses={'realpersona':.25,'jmrd':.05}
    assert abs(genres['human-chat']-sum(source_masses.values()))<1e-12
    assert {k[2] for k in counts if k[0]=='human-chat'}==set(source_masses)
    weights={k:(source_masses[k[3]] if k[0]=='human-chat' else genres[k[0]])*VIEWS[k[1]]*len(v)/counts[(k[0],k[1],k[3])] for k,v in strata.items()}
    masses={w:sum(p for k,p in weights.items() if k[2]==w) for w in WIDTHS}
    assert abs(sum(masses.values())-1)<1e-10
    return strata,weights,masses

def draw(rng,batch,strata,weights,masses):
    width=rng.choices(list(masses),weights=list(masses.values()),k=1)[0]
    keys=[k for k in strata if k[2]==width]
    chosen=rng.choices(keys,weights=[weights[k] for k in keys],k=batch)
    return width,[rng.choice(strata[k]) for k in chosen]
