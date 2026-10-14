import sys, numpy as np, pandas as pd
sys.path.insert(0, '/home/user/fly-escape/sim'); from lif import load, run
D, ANN = sys.argv[1], sys.argv[2]
ids, W = load(D); idx = {r: i for i, r in enumerate(ids)}
a = pd.read_csv(ANN, sep='\t', low_memory=False)
a = a[a.root_id.isin(idx)]
def grp(types, side):
    m = a[a.cell_type.isin(types) & (a.side == side)]
    return np.array([idx[r] for r in m.root_id])
dn = a[a.super_class == 'descending']
dn_idx = np.array([idx[r] for r in dn.root_id]); dn_name = (dn.cell_type.fillna('?') + '_' + dn.side.str[0]).values
WATCH = ['DNa01', 'DNa02', 'DNa03', 'DNb05', 'DNg13', 'DNp09', 'DNp01', 'DNb06', 'DNa11']
MOD = {k: v for k, v in [('ON_Mi1', ['Mi1']), ('ON_Tm3', ['Tm3']), ('L1', ['L1']), ('L2', ['L2']), ('looming_LPLC2', ['LPLC2'])]}

for mod, types in MOD.items():
    res = {}
    for side in ['left', 'right']:
        s = grp(types, side)
        c, _ = run(W, s, 60, t_ms=400, seed=1)
        res[side] = c[dn_idx]
        print(f'{mod} {side}: {len(s)} input neurons, active DNs {np.count_nonzero(res[side])}', flush=True)
    for t in WATCH:
        L = res['left'][dn_name == f'{t}_l']; R = res['right'][dn_name == f'{t}_r']
        Lc = res['left'][dn_name == f'{t}_r']; Rc = res['right'][dn_name == f'{t}_l']
        if len(L): print(f'   {t}: stimL -> L{L.sum()} R{Lc.sum()}  | stimR -> L{Rc.sum()} R{R.sum()}')
    # most lateralized DN pairs: (ipsi - contra) consistent on both sides
    d = res['left'] - res['right']
    order = np.argsort(-np.abs(d))[:8]
    print('   top differential DNs:', [(dn_name[i], int(res['left'][i]), int(res['right'][i])) for i in order])
