"""Taste, grooming, silenced-escape tables + spike-propagation data for the 3D brain view."""
import sys, json, itertools, numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, '/home/user/fly-escape/sim'); from lif import load, run
D, ANN, OUT, NP = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
T = 300
ids, W = load(D); idx = {r: i for i, r in enumerate(ids)}
a = pd.read_csv(ANN, sep='\t', low_memory=False); a = a[a.root_id.isin(idx)].copy(); a['i'] = a.root_id.map(idx)
def sub(s): return a[a.cell_sub_class == s].i.values
def typ(t, side=None):
    m = a[a.cell_type.isin(t)] if isinstance(t, list) else a[a.cell_type.fillna('').str.match(t)]
    if side: m = m[m.side == side]
    return m.i.values
# readouts found by discover.py (strongest motor/descending targets)
R_TASTE = {'feedMN_L': typ(['CB0871', 'CB0701'], 'left'), 'feedMN_R': typ(['CB0871', 'CB0701'], 'right'),
           'DNge059_L': typ(['DNge059'], 'left'), 'DNge059_R': typ(['DNge059'], 'right'),
           'DNg67_L': typ(['DNg67'], 'left'), 'DNg67_R': typ(['DNg67'], 'right')}
R_GROOM = {'groomMN_L': typ(['CB0810'], 'left'), 'groomMN_R': typ(['CB0810'], 'right'),
           'DNg84_L': typ(['DNg84'], 'left'), 'DNg84_R': typ(['DNg84'], 'right'),
           'DNg35_L': typ(['DNg35'], 'left'), 'DNg35_R': typ(['DNg35'], 'right'),
           'DNg15_L': typ(['DNg15'], 'left'), 'DNg15_R': typ(['DNg15'], 'right')}
R_LOOM = {f'{t}_{s[0].upper()}': typ([t], s) for t in ['DNp01', 'DNp04'] for s in ('left', 'right')}
SUGAR, BITTER, WATER = sub('sugar'), sub('bitter'), sub('water')
ANT = typ(r'BM_Ant'); JOCE = typ(r'JO-C|JO-E')
LOOM = {s: typ(['LPLC2', 'LC4'], s) for s in ('left', 'right')}
SIL = {'none': [], 'GF': typ(['DNp01']), 'DNp04': typ(['DNp04']), 'LPLC2': typ(['LPLC2']), 'LC4': typ(['LC4'])}
LEV = [0, 15, 30, 50, 75, 100]
def ro(c, R): return {k: float(c[v].mean() / (T / 1000)) if len(v) else 0.0 for k, v in R.items()}
def job(j):
    kind = j[0]
    if kind == 'taste':
        _, x, y = j; stim = np.r_[SUGAR, BITTER]; rates = np.r_[np.full(SUGAR.size, x), np.full(BITTER.size, y)]
        c, _ = run(W, stim, rates, t_ms=T, seed=5); return j, ro(c, R_TASTE)
    if kind == 'water':
        _, x = j; c, _ = run(W, WATER, x, t_ms=T, seed=5); return j, ro(c, R_TASTE)
    if kind == 'groom':
        _, x, y = j; stim = np.r_[ANT, JOCE]; rates = np.r_[np.full(ANT.size, x), np.full(JOCE.size, y)]
        c, _ = run(W, stim, rates, t_ms=T, seed=5); return j, ro(c, R_GROOM)
    if kind == 'sil':
        _, name, l, r = j; stim = np.r_[LOOM['left'], LOOM['right']]; rates = np.r_[np.full(LOOM['left'].size, l), np.full(LOOM['right'].size, r)]
        c, _ = run(W, stim, rates, t_ms=T, seed=7, silence=SIL[name]); return j, ro(c, R_LOOM)
    if kind == 'wave':
        _, name = j
        stim, rate = {'loom': (np.r_[LOOM['left'], LOOM['right']], 100), 'sugar': (SUGAR, 100), 'antenna': (ANT, 100),
                      'light_left': (typ(['Tm3'], 'left'), 60)}[name]
        c, tf = run(W, stim, rate, t_ms=150, seed=11, first=True)
        act = np.flatnonzero(c > 0)
        return j, {'idx': act.tolist(), 't': [round(float(x), 1) for x in tf[act]], 'n': c[act].tolist(), 'stim': np.asarray(stim).tolist()}
jobs = [('taste', x, y) for x, y in itertools.product(LEV, LEV)] + [('water', x) for x in LEV] + \
       [('groom', x, y) for x, y in itertools.product(LEV, LEV)] + \
       [('sil', s, l, r) for s in SIL if s != 'none' for l, r in itertools.product(LEV, LEV)] + \
       [('wave', w) for w in ['loom', 'sugar', 'antenna', 'light_left']]
with Pool(NP) as p: res = p.map(job, jobs, chunksize=1)
out = {'levels': LEV, 'taste': {}, 'water': {}, 'groom': {}, 'silence': {s: {} for s in SIL if s != 'none'}, 'waves': {},
       'readouts': {'taste': list(R_TASTE), 'groom': list(R_GROOM), 'loom': list(R_LOOM)},
       'counts': {'sugar': int(SUGAR.size), 'bitter': int(BITTER.size), 'water': int(WATER.size), 'antenna_bristle': int(ANT.size), 'JO_CE': int(JOCE.size),
                  'silence': {k: int(len(v)) for k, v in SIL.items()}}}
used = set()
for j, r in res:
    k = j[0]
    if k in ('taste', 'groom'): out[k][f'{j[1]},{j[2]}'] = r
    elif k == 'water': out['water'][str(j[1])] = r
    elif k == 'sil': out['silence'][j[1]][f'{j[2]},{j[3]}'] = r
    else: out['waves'][j[1]] = r; used.update(r['idx']); used.update(r['stim'])
# positions: all wave neurons + random background sample for the brain shape
pos = a.set_index('i')[['pos_x', 'pos_y', 'pos_z', 'super_class', 'cell_type']]
rng = np.random.default_rng(0)
bg = rng.choice(pos.index.values, 24000, replace=False)
keep = sorted(set(bg.tolist()) | used)
P = pos.loc[[k for k in keep if k in pos.index]]
cls = sorted(P.super_class.fillna('other').unique())
out['neurons'] = {'i': P.index.tolist(), 'x': P.pos_x.astype(int).tolist(), 'y': P.pos_y.astype(int).tolist(), 'z': P.pos_z.astype(int).tolist(),
                  'cls': [cls.index(c) for c in P.super_class.fillna('other')], 'type': P.cell_type.fillna('').tolist()}
out['classes'] = cls
json.dump(out, open(OUT, 'w'), separators=(',', ':'))
print('done', len(res), 'neurons in 3D set', len(P))
