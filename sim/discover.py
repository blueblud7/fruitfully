import sys, numpy as np, pandas as pd
sys.path.insert(0, '/home/user/fly-escape/sim'); from lif import load, run
D, ANN = sys.argv[1], sys.argv[2]
ids, W = load(D); idx = {r: i for i, r in enumerate(ids)}
a = pd.read_csv(ANN, sep='\t', low_memory=False); a = a[a.root_id.isin(idx)].copy()
a['i'] = a.root_id.map(idx)
name = (a.cell_type.fillna(a.hemibrain_type).fillna('?') + '_' + a.side.fillna('?').str[0]).values
ii = a.i.values; sc = a.super_class.values
def sub(s): return a[a.cell_sub_class == s].i.values
def typ(prefix): return a[a.cell_type.fillna('').str.match(prefix)].i.values
STIM = {'sugar': sub('sugar'), 'bitter': sub('bitter'), 'water': sub('water'),
        'JO-CE': typ(r'JO-C|JO-E'), 'BM_Ant': typ(r'BM_Ant'), 'grooming_sub': sub('grooming')}
for k, s in STIM.items():
    c, _ = run(W, s, 100, t_ms=300, seed=3)
    out = []
    for cls in ['motor', 'descending']:
        m = sc == cls; order = np.argsort(-c[ii[m]])[:8]
        out.append(cls + ': ' + ', '.join(f'{name[m][j]}({ii[m][j]})={c[ii[m][j]]/0.3:.0f}Hz' for j in order if c[ii[m][j]] > 0))
    print(f'== {k} ({len(s)} neurons) active={np.count_nonzero(c)}'); print('  ' + '\n  '.join(out), flush=True)
# sugar + bitter together: does bitter suppress sugar-driven motor output?
c, _ = run(W, np.r_[STIM['sugar'], STIM['bitter']], 100, t_ms=300, seed=3)
m = sc == 'motor'; order = np.argsort(-c[ii[m]])[:6]
print('== sugar+bitter motor:', ', '.join(f'{name[m][j]}={c[ii[m][j]]/0.3:.0f}Hz' for j in order))
