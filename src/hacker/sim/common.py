"""Shared setup for 신경 해커: connectome, annotations, stimuli, readouts."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, '/home/user/fly-escape/sim'); from lif import load, run  # noqa
SP = '/tmp/claude-0/-home-user/cbbcfdcd-898b-5509-9a11-b1f16acb006d/scratchpad'
D = os.environ.get('HK_DATA', SP + '/dbm2')
ANN = os.environ.get('HK_ANN', SP + '/ann/flywire_annotations/supplemental_files/Supplemental_file1_neuron_annotations.tsv')
T = 300  # ms per run
ids, W = load(D); idx = {r: i for i, r in enumerate(ids)}
a = pd.read_csv(ANN, sep='\t', low_memory=False); a = a[a.root_id.isin(idx)].copy(); a['i'] = a.root_id.map(idx)
a['ct'] = a.cell_type.fillna('')
def sub(s): return a[a.cell_sub_class == s].i.values
def typ(t, side=None):
    m = a[a.ct.isin(t)] if isinstance(t, (list, tuple)) else a[a.ct.str.match(t)]
    if side: m = m[m.side == side]
    return np.sort(m.i.values)
def tside(t, side): return typ([t], side)
SUGAR, BITTER = sub('sugar'), sub('bitter')
ANT = typ(r'BM_Ant')
LOOM = {s: typ(['LPLC2', 'LC4'], s) for s in ('left', 'right')}
READ = {
    'GF_L': tside('DNp01', 'left'), 'GF_R': tside('DNp01', 'right'),
    'DNp04_L': tside('DNp04', 'left'), 'DNp04_R': tside('DNp04', 'right'),
    'feed_L': typ(['CB0871', 'CB0701'], 'left'), 'feed_R': typ(['CB0871', 'CB0701'], 'right'),
    'groom_L': tside('CB0810', 'left'), 'groom_R': tside('CB0810', 'right'),
}
def readout(c):
    return {k: round(float(c[v].mean() / (T / 1000)), 2) if len(v) else 0.0 for k, v in READ.items()}
SCEN = {
    'loom':   lambda: (np.r_[LOOM['left'], LOOM['right']], 100.0),
    'loomL':  lambda: (LOOM['left'], 100.0),
    'sugar':  lambda: (SUGAR, 100.0),
    'sb':     lambda: (np.r_[SUGAR, BITTER], 100.0),
    'bitter': lambda: (BITTER, 100.0),
    'ant':    lambda: (ANT, 100.0),
    'sugarloom': lambda: (np.r_[SUGAR, LOOM['left'], LOOM['right']], 100.0),
    'none':   lambda: (np.array([], dtype=int), 0.0),
}
def neurons_of(spec):
    """spec: 'TYPE' or 'TYPE@left' / 'TYPE@right' or 'sub:sugar'."""
    if spec.startswith('sub:'): return sub(spec[4:])
    if spec.startswith('re:'): return typ(spec[3:])
    if '@' in spec:
        t, s = spec.split('@'); return tside(t, s)
    return typ([spec])
def simulate(scen, silence=(), activate=(), seed=7, act_rate=100.0, t_ms=T):
    stim, rate = SCEN[scen]()
    rates = np.full(len(stim), rate)
    for sp in activate:
        n = neurons_of(sp); stim = np.r_[stim, n]; rates = np.r_[rates, np.full(len(n), act_rate)]
    sil = np.unique(np.concatenate([neurons_of(s) for s in silence])) if silence else None
    if len(stim) == 0: stim = np.array([0]); rates = np.array([0.0])
    c, _ = run(W, stim.astype(int), rates, t_ms=t_ms, seed=seed, silence=sil)
    return c
