"""Precompute brain response tables from the whole-connectome LIF for the browser lab."""
import sys, json, itertools, numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, '/home/user/fly-escape/sim'); from lif import load, run
D, ANN, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
T = 300  # ms per condition
ids, W = load(D); idx = {r: i for i, r in enumerate(ids)}
a = pd.read_csv(ANN, sep='\t', low_memory=False); a = a[a.root_id.isin(idx)]
def grp(types, side=None):
    m = a[a.cell_type.isin(types)]
    if side: m = m[m.side == side]
    return np.array([idx[r] for r in m.root_id])
def one(types_side, name):
    return {s: grp(types_side, s) for s in ('left', 'right')}
READ = {}
for t in ['DNp01', 'DNp04', 'DNp07', 'DNb05', 'DNbe001', 'DNa02', 'DNg13', 'DNp18', 'DNg56']:
    for s in ('left', 'right'):
        READ[f'{t}_{s[0].upper()}'] = grp([t], s)
NAMES = list(READ)
def readout(c):
    return {k: float(c[v].mean() / (T / 1000)) for k, v in READ.items()}  # Hz
LOOM = one(['LPLC2', 'LC4'], 'loom'); LIGHT = one(['Tm3'], 'light')
ODOR = grp(['ORN_DM1', 'ORN_DM2', 'ORN_DM4', 'ORN_VM2', 'ORN_VA2'])
LEV2 = [0, 15, 30, 50, 75, 100]
def job(arg):
    kind, l, r = arg
    if kind == 'odor':
        stim, rates = ODOR, np.full(ODOR.size, float(l))
    else:
        g = LOOM if kind == 'loom' else LIGHT
        stim = np.r_[g['left'], g['right']]; rates = np.r_[np.full(g['left'].size, float(l)), np.full(g['right'].size, float(r))]
    c, _ = run(W, stim, rates, t_ms=T, seed=7)
    return kind, l, r, readout(c)
jobs = [(k, l, r) for k in ('loom', 'light') for l, r in itertools.product(LEV2, LEV2)] + [('odor', l, 0) for l in [0, 5, 10, 20, 30, 45, 60, 80, 100]]
with Pool(int(sys.argv[4])) as p:
    res = p.map(job, jobs, chunksize=1)
out = {'levels2d': LEV2, 'odor_levels': [0, 5, 10, 20, 30, 45, 60, 80, 100], 'readouts': NAMES,
       'loom': {}, 'light': {}, 'odor': {},
       'meta': {'connectome': 'FlyWire 783 (philshiu/Drosophila_brain_model)', 'neurons': int(len(ids)), 'synapse_rows': int(W.nnz),
                'model': 'LIF, Shiu et al. 2024 params', 'sim_ms': T,
                'inputs': {'loom': 'LPLC2+LC4 per side', 'light': 'Tm3 (ON pathway) per side', 'odor': 'ORN DM1/DM2/DM4/VM2/VA2 both sides'}}}
for kind, l, r, ro in res:
    key = f'{l}' if kind == 'odor' else f'{l},{r}'
    out[kind][key] = ro
json.dump(out, open(OUT, 'w'), indent=0)
print('done', len(res))
