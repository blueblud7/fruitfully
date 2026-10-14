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
ODOR_LV = [0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.4, 1.6, 2.0]
SEEDS = 8
# ORN types differ in sensitivity: half-activation concentration per glomerulus (spread over 2 decades)
ORN_TYPES = ['ORN_DM1', 'ORN_DM4', 'ORN_DM2', 'ORN_VM2', 'ORN_VA2']
ORN_K = [10**-4.5, 10**-4, 10**-3.5, 10**-3, 10**-2.5]
ORN_MAX = 4.0  # Hz per ORN at saturation (model is very sensitive: ~1 Hz/ORN crosses threshold)
def job(arg):
    kind, l, r, sd = arg
    if kind == 'odor':
        parts = [grp([t]) for t in ORN_TYPES]
        stim = np.concatenate(parts)
        rates = np.full(stim.size, float(l))  # uniform ORN rate (Hz); adaptation/log transduction handled in the browser
    else:
        g = LOOM if kind == 'loom' else LIGHT
        stim = np.r_[g['left'], g['right']]; rates = np.r_[np.full(g['left'].size, float(l)), np.full(g['right'].size, float(r))]
    c, _ = run(W, stim, rates, t_ms=T, seed=sd)
    return kind, l, r, readout(c)
jobs = [('odor', l, 0, sd) for l in ODOR_LV for sd in range(SEEDS)]
with Pool(int(sys.argv[4])) as p:
    res = p.map(job, jobs, chunksize=1)
out = {'levels2d': LEV2, 'odor_levels': ODOR_LV, 'readouts': NAMES,
       'loom': {}, 'light': {}, 'odor': {},
       'meta': {'connectome': 'FlyWire 783 (philshiu/Drosophila_brain_model)', 'neurons': int(len(ids)), 'synapse_rows': int(W.nnz),
                'model': 'LIF, Shiu et al. 2024 params', 'sim_ms': T,
                'inputs': {'loom': 'LPLC2+LC4 per side', 'light': 'Tm3 (ON pathway) per side', 'odor': 'ORN DM1/DM2/DM4/VM2/VA2 both sides'}}}
acc = {}
for kind, l, r, ro in res:
    a = acc.setdefault(str(l), {k: 0.0 for k in ro})
    for k, v in ro.items(): a[k] += v / SEEDS
out['odor'] = acc
old=json.load(open(OUT)); old['odor']=out['odor']; old['odor_levels']=ODOR_LV; old['meta']['inputs']['odor']='ORN DM1/DM4/DM2/VM2/VA2 both sides; uniform rate per ORN (Hz) = level, mean of 8 Poisson seeds; browser maps path distance to 0.4-1.6 Hz (adapted, log transduction)'; json.dump(old, open(OUT, 'w'), indent=0)
print('done', len(res))
