"""Event-driven LIF over the FlyWire 783 connectome.

Same equations/parameters as Shiu et al. (philshiu/Drosophila_brain_model, model.py):
  dv/dt = (v0 - v + g)/t_mbr ; dg/dt = -g/tau ; spike -> g_post += w (delay 1.8 ms)
"""
import sys, numpy as np, pandas as pd
from scipy.sparse import csr_matrix

V0, VRST, VTH = -52.0, -52.0, -45.0   # mV
TMBR, TAU, TRFC, TDLY = 20.0, 5.0, 2.2, 1.8  # ms
WSYN, FPOI = 0.275, 250               # mV per synapse, Poisson scaling
DT = 0.1                              # ms

def load(data_dir):
    c = pd.read_parquet(f'{data_dir}/Connectivity_783.parquet')
    ids = pd.read_csv(f'{data_dir}/Completeness_783.csv').iloc[:, 0].values
    n = len(ids)
    # W[post, pre]: column = presynaptic neuron, so a spike adds W[:, pre]
    W = csr_matrix((c['Excitatory x Connectivity'].values * WSYN,
                    (c['Presynaptic_Index'].values, c['Postsynaptic_Index'].values)), shape=(n, n))  # rows = pre
    return ids, W.tocsr()

def run(W, stim, rates_hz, t_ms=500, seed=0, record=None, silence=None, first=False):
    """stim: array of neuron indices; rates_hz: Poisson rate per stim neuron (scalar or array).
    Returns spike counts per neuron."""
    rng = np.random.default_rng(seed)
    n = W.shape[0]
    v = np.full(n, V0); g = np.zeros(n); rfc_until = np.zeros(n)
    dly = int(round(TDLY / DT)); buf = np.zeros((dly + 1, n))
    counts = np.zeros(n, dtype=np.int32)
    t_first = np.full(n, -1.0)
    sil = np.zeros(n, bool)
    if silence is not None and len(silence): sil[np.asarray(silence)] = True
    stim = np.asarray(stim); rates = np.broadcast_to(np.asarray(rates_hz, float), stim.shape)
    p = rates * DT / 1000.0
    steps = int(t_ms / DT)
    trace = []
    for k in range(steps):
        t = k * DT
        g += buf[k % (dly + 1)]; buf[k % (dly + 1)] = 0
        # Poisson drive (stimulated neurons have no refractory period in the original model)
        hit = stim[rng.random(stim.size) < p]
        g[hit] += WSYN * FPOI
        active = t >= rfc_until
        v[active] += DT * (V0 - v[active] + g[active]) / TMBR
        g[active] -= DT * g[active] / TAU
        v[sil] = V0; g[sil] = 0
        sp = np.flatnonzero(v > VTH)
        if sp.size:
            counts[sp] += 1
            nf = sp[t_first[sp] < 0]; t_first[nf] = t
            v[sp] = VRST; g[sp] = 0
            nonstim = ~np.isin(sp, stim)
            rfc_until[sp[nonstim]] = t + TRFC
            row = W[sp].sum(axis=0).A1          # summed outgoing weights
            buf[(k + dly) % (dly + 1)] += row
        if record is not None and k % 10 == 0:
            trace.append(v[record].copy())
    if first: return counts, t_first
    return counts, (np.array(trace) if record is not None else None)
