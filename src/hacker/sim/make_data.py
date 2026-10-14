"""Assemble hacker_data.json from runs.jsonl (whole-brain LIF results) + annotations + connectome.
No simulation here: every readout in the output is copied from runs.jsonl."""
import json, os, sys, itertools, numpy as np, pandas as pd
from stages import STAGES
from run_stages import load_cache, stage_keys, key
from texts import TEXT, SCEN_TXT, RLAB, HONEST, TH, PARAM
SP = '/tmp/claude-0/-home-user/cbbcfdcd-898b-5509-9a11-b1f16acb006d/scratchpad'
D = SP + '/dbm2'; ANN = SP + '/ann/flywire_annotations/supplemental_files/Supplemental_file1_neuron_annotations.tsv'
OUT = '/home/user/fruitfly-games/hacker/hacker_data.json'
VSEEDS = [8, 9, 10]
ids = pd.read_csv(f'{D}/Completeness_783.csv').iloc[:, 0].values; idx = {r: i for i, r in enumerate(ids)}
a = pd.read_csv(ANN, sep='\t', low_memory=False); a = a[a.root_id.isin(idx)].copy(); a['i'] = a.root_id.map(idx); a['ct'] = a.cell_type.fillna('')
con = pd.read_parquet(f'{D}/Connectivity_783.parquet', columns=['Presynaptic_Index', 'Postsynaptic_Index', 'Connectivity'])
C = load_cache()
def nset(spec):
    if '@' in spec: t, s = spec.split('@'); return a[(a.ct == t) & (a.side == s)]
    return a[a.ct == spec]
RMAP = {'GF': ['DNp01'], 'P4': ['DNp04'], 'FD': ['CB0871', 'CB0701'], 'GR': ['CB0810']}
def rkeys(r):  # runs.jsonl readout -> short keys
    m = {'GF_L': 'GF_L', 'GF_R': 'GF_R', 'DNp04_L': 'P4_L', 'DNp04_R': 'P4_R', 'feed_L': 'FD_L', 'feed_R': 'FD_R', 'groom_L': 'GR_L', 'groom_R': 'GR_R'}
    return {m[k]: round(v, 1) for k, v in r.items()}
def avg(r, k): return (r[k + '_L'] + r[k + '_R']) / 2
def goal_ok(g, r, p):
    gf, fd, gr = avg(r, 'GF'), avg(r, 'FD'), avg(r, 'GR')
    if g == 'noescape': return gf <= TH['GF']
    if g == 'escape': return gf > TH['GF']
    if g == 'eat': return fd >= TH['FEED']
    if g == 'noeat': return fd < TH['FEED']
    if g == 'groom': return gr >= TH['GROOM']
    if g == 'nogroom': return gr < TH['GROOM']
    if g == 'feast': return fd >= p
    if g == 'strong': return gf >= p
    if g == 'oneside':
        x, y = r['P4_L'], r['P4_R']; mx = max(x, y)
        return gf > TH['GF'] and mx > 0 and min(x, y) <= p * mx
    if g == 'eat_noescape': return fd >= TH['FEED'] and gf <= TH['GF']
READK = {'noescape': ['GF'], 'escape': ['GF'], 'strong': ['GF'], 'oneside': ['GF', 'P4_L', 'P4_R'], 'eat': ['FD'], 'noeat': ['FD'],
         'feast': ['FD'], 'groom': ['GR'], 'nogroom': ['GR'], 'eat_noescape': ['FD', 'GF']}
NT_KO = {'acetylcholine': '아세틸콜린(흥분)', 'gaba': 'GABA(억제)', 'glutamate': '글루탐산(대개 억제)', 'dopamine': '도파민', 'serotonin': '세로토닌', 'octopamine': '옥토파민'}
SC_KO = {'central': '중앙뇌 사이뉴런', 'descending': '하행 뉴런(뇌→몸)', 'ascending': '상행 뉴런(몸→뇌)', 'visual_projection': '시각 투사 뉴런', 'optic': '시각엽', 'sensory': '감각 뉴런', 'motor': '운동 뉴런', 'visual_centrifugal': '시각 원심 뉴런', 'endocrine': '내분비'}
SIDE_KO = {'left': '왼쪽', 'right': '오른쪽', 'center': '가운데'}
# ---- 3D positions: background sample + every special neuron
rng = np.random.default_rng(0)
bg = rng.choice(a.i.values, 16000, replace=False).tolist()
special = []
stim_specs = {'loom': ['LPLC2', 'LC4'], 'sugar': ['sub:sugar'], 'sb': ['sub:sugar', 'sub:bitter'], 'ant': ['re:BM_Ant'], 'sugarloom': ['sub:sugar', 'LPLC2', 'LC4'], 'none': []}
def spec_rows(s):
    if s.startswith('sub:'): return a[a.cell_sub_class == s[4:]]
    if s.startswith('re:'): return a[a.ct.str.match(s[3:])]
    return nset(s)
stimN = {k: sorted(set(np.concatenate([spec_rows(s).i.values for s in v]).tolist())) if v else [] for k, v in stim_specs.items()}
readN = {k: sorted(a[a.ct.isin(v)].i.values.tolist()) for k, v in RMAP.items()}
for v in list(stimN.values()) + list(readN.values()): special += v
for st in STAGES:
    for c in st['cands']: special += nset(c).i.values.tolist()
order = bg + sorted(set(special) - set(bg))
local = {g: k for k, g in enumerate(order)}
P = a.set_index('i').loc[order]
xs, ys, zs = P.pos_x.values.astype(float), P.pos_y.values.astype(float), P.pos_z.values.astype(float) * 10
cx, cy, cz = [(np.min(v) + np.max(v)) / 2 for v in (xs, ys, zs)]
s = 1000 / ((np.max(xs) - np.min(xs)) / 2)
pos = np.round(np.c_[(xs - cx) * s, (ys - cy) * s, (zs - cz) * s]).astype(int).ravel().tolist()
side_of = a.set_index('i').side
readSide = {}
for k, v in readN.items():
    for g in v: readSide[local[g]] = 'L' if side_of[g] == 'left' else 'R'
# ---- stages
stages, report = [], []
for st in STAGES:
    p = PARAM.get(st['id'])
    res = {}
    for k in stage_keys(st):
        sp = k.split('|'); combo = [x for x in (sp[1] or sp[2]).split(',') if x]
        res['+'.join(sorted(combo))] = rkeys(C[k]['r'])
    base = res['']
    sols = sorted([c for c, r in res.items() if c and goal_ok(st['goal'], r, p)], key=lambda c: (c.count('+'), c))
    assert sols, st['id'] + ' unsolvable'
    assert not goal_ok(st['goal'], base, p), st['id'] + ' solved by doing nothing'
    minK = min(c.count('+') + 1 for c in sols)
    # robustness on extra seeds
    rob = {}
    for c in [''] + sols:
        combo = c.split('+') if c else []
        sil, act = (combo, ()) if st['mode'] == 'sil' else ((), combo)
        vals = []
        for sd in VSEEDS:
            kk = key(st['scen'], sil, act, sd)
            if kk in C: vals.append(goal_ok(st['goal'], rkeys(C[kk]['r']), p))
        if vals: rob[c] = vals
    R = set(sum((RMAP[x[:2]] for x in READK[st['goal']]), []))
    rid = a[a.ct.isin(R)].i.values
    cands = []
    for c in st['cands']:
        rows = nset(c); nt = rows.top_nt.fillna('?').mode().iat[0]
        syn = int(con[con.Presynaptic_Index.isin(rows.i.values) & con.Postsynaptic_Index.isin(rid)].Connectivity.sum())
        scs = rows.super_class.fillna('?').mode().iat[0]
        sides = rows.side.fillna('?').value_counts()
        sd = ' · '.join(f"{SIDE_KO.get(k, k)} {v}" for k, v in sides.items())
        t, _, sside = c.partition('@')
        label = t + (f" ({SIDE_KO[sside]})" if sside else '')
        desc = f"{SC_KO.get(scs, scs)} · {sd}" + (f" · 판독 뉴런에 직접 시냅스 {syn}개" if syn else '')
        cands.append({'id': c, 'label': label, 'n': int(len(rows)), 'nt': nt, 'ntKo': NT_KO.get(nt, nt),
                      'ntSign': -1 if nt in ('gaba', 'glutamate') else 1 if nt == 'acetylcholine' else 0, 'desc': desc, 'syn': syn,
                      'pts': [local[g] for g in rows.i.values]})
    T = TEXT[st['id']]
    stages.append({'id': st['id'], 'scen': st['scen'], 'mode': st['mode'], 'K': st['K'], 'goal': st['goal'], 'param': p,
                   'title': T['title'], 'story': T['story'], 'why': T['why'], 'note': T.get('note', ''),
                   'readKeys': READK[st['goal']], 'cands': cands, 'res': res, 'sols': sols, 'minK': minK, 'robust': rob})
    report.append((st['id'], T['title'], minK, sols[:6], {c: v for c, v in rob.items()}))
order_ids = [x for x in TEXT['_order']]
stages.sort(key=lambda s: order_ids.index(s['id']))
out = {'th': TH, 'scen': SCEN_TXT, 'rlab': RLAB, 'honest': HONEST, 'stages': stages, 'base': {s['id']: s['res'][''] for s in stages},
       'nb': {'p': pos, 'bg': len(bg)}, 'stimPts': {k: [local[g] for g in v] for k, v in stimN.items()},
       'readPts': {k: [local[g] for g in v] for k, v in readN.items()}, 'readSide': readSide,
       'meta': {'connectome': 'FlyWire 783', 'neurons': int(len(ids)), 'model': 'LIF, Shiu et al. 2024', 'sim_ms': 300, 'seed': 7, 'verify_seeds': VSEEDS,
                'runs': len(C), 'cpu_sec': round(sum(r['sec'] for r in C.values()))}}
json.dump(out, open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'))
for r in report: print(r)
print('wrote', OUT, os.path.getsize(OUT), 'bytes; runs', len(C))
