"""Step 1: rank candidate cell types per scenario, then screen single knockouts / activations
with the full-brain LIF. Output: discover.json"""
import json, sys, time, numpy as np
from multiprocessing import Pool
from common import *
from scipy.sparse import diags
OUT = sys.argv[1]; NS = int(sys.argv[2]) if len(sys.argv) > 2 else 24
TARGET = {'loom': ['GF_L', 'GF_R'], 'sb': ['feed_L', 'feed_R'], 'sugar': ['feed_L', 'feed_R'], 'ant': ['groom_L', 'groom_R']}
def base(s): return s, simulate(s)
def job(j):
    kind, scen, spec = j
    c = simulate(scen, silence=[spec]) if kind == 'sil' else simulate('none', activate=[spec])
    return j, readout(c)
if __name__ == '__main__':
    t0 = time.time()
    with Pool(3) as p: B = dict(p.map(base, list(TARGET)))
    ct = a.set_index('i').ct; nt = a.set_index('i').top_nt.fillna('?')
    Wa = W.tocsr()
    res = {'baseline': {s: readout(c) for s, c in B.items()}, 'rank': {}, 'screen': {}}
    jobs = []
    for s, keys in TARGET.items():
        c = B[s]; act = (c > 0).astype(float)
        R = np.unique(np.concatenate([READ[k] for k in keys]))
        wR = np.asarray(Wa[:, R].sum(axis=1)).ravel()                 # direct weight of each neuron onto readout
        two = Wa @ (act * wR)                                         # via active intermediates
        score = c * (wR + 0.1 * two)
        df = pd.DataFrame({'ct': ct.reindex(np.arange(len(ids))).fillna('').values, 'score': score, 'rate': c / 0.3, 'act': c > 0})
        df = df[df.ct != '']
        g = df.groupby('ct').agg(score=('score', 'sum'), n=('act', 'size'), nact=('act', 'sum'), rate=('rate', 'mean'))
        g = g[g.nact > 0]; g['abs'] = g.score.abs()
        stimtypes = set(ct.reindex(SCEN[s]()[0]).values)
        g = g[~g.index.isin(stimtypes)].sort_values('abs', ascending=False)
        top = g.head(NS)
        res['rank'][s] = [{'type': t, 'score': round(float(r.score), 1), 'n': int(r.n), 'nact': int(r.nact), 'rate': round(float(r.rate), 1),
                           'nt': nt[a[a.ct == t].i.values].mode().iat[0]} for t, r in top.iterrows()]
        jobs += [('sil', s, t) for t in top.index]
        # activation candidates: active positive contributors (for the no-stimulus stages)
        pos = g[g.score > 0].head(10)
        jobs += [('act', s, t) for t in pos.index]
    print('baselines done', time.time() - t0, len(jobs), 'jobs', flush=True)
    with Pool(3) as p:
        for j, r in p.imap_unordered(job, jobs):
            res['screen'].setdefault(j[1], {}).setdefault(j[0], {})[j[2]] = r
            print(j, {k: r[k] for k in TARGET[j[1]]}, flush=True)
    res['sec'] = time.time() - t0
    json.dump(res, open(OUT, 'w'), indent=1)
    print('done', res['sec'])
