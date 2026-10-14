import sys, time, numpy as np, pandas as pd
sys.path.insert(0, '/home/user/fly-escape/sim'); from lif import load, run
D = sys.argv[1]; ANN = sys.argv[2]
ids, W = load(D); idx = {r: i for i, r in enumerate(ids)}
a = pd.read_csv(ANN, sep='\t', low_memory=False)
def group(t, side=None):
    m = a[a.cell_type == t]
    if side: m = m[m.side == side]
    return np.array([idx[r] for r in m.root_id if r in idx])
GF = group('DNp01'); print('GF idx', GF, 'sides', a[a.cell_type=='DNp01'].side.tolist())
for name, stim in [('none', np.array([], int)), ('LPLC2', group('LPLC2')), ('LC4', group('LC4')), ('LPLC2+LC4', np.r_[group('LPLC2'), group('LC4')])]:
    for r in ([0] if name=='none' else [20, 50, 100]):
        t0 = time.time(); c, _ = run(W, stim, r, t_ms=300)
        print(f'{name:10s} {r:4d}Hz -> GF spikes {c[GF].tolist()} (rate {c[GF].mean()/0.3:.0f}Hz)  active neurons {np.count_nonzero(c)}  [{time.time()-t0:.0f}s]', flush=True)
