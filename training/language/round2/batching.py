"""Group padding widths; preserve each original row's sampling probability."""
import collections

WIDTHS=(64,128,256)
VIEWS={0:.5,.15:.25,.3:.25}

def sampler(rows,genres):
    counts=collections.Counter((r['site'],r['variant']) for r in rows)
    strata=collections.defaultdict(list)
    for r in rows:
        width=next(w for w in WIDTHS if r['length']-1<=w)
        strata[(r['site'],r['variant'],width)].append(r)
    weights={k:genres[k[0]]*VIEWS[k[1]]*len(v)/counts[k[:2]] for k,v in strata.items()}
    masses={w:sum(p for k,p in weights.items() if k[2]==w) for w in WIDTHS}
    assert abs(sum(masses.values())-1)<1e-10
    return strata,weights,masses

def draw(rng,batch,strata,weights,masses):
    width=rng.choices(list(masses),weights=list(masses.values()),k=1)[0]
    keys=[k for k in strata if k[2]==width]
    chosen=rng.choices(keys,weights=[weights[k] for k in keys],k=batch)
    return width,[rng.choice(strata[k]) for k in chosen]
