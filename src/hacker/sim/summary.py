import json, sys
from stages import STAGES
from run_stages import load_cache, stage_keys
C = load_cache()
for st in STAGES:
    keys = stage_keys(st)
    print('=====', st['id'], st['scen'], st['goal'], st['mode'], 'K', st['K'], f"{sum(k in C for k in keys)}/{len(keys)}")
    rows = []
    for k in keys:
        if k not in C: continue
        r = C[k]['r']; s = k.split('|')
        combo = s[1] or s[2] or '-'
        gf = (r['GF_L'] + r['GF_R']) / 2; fd = (r['feed_L'] + r['feed_R']) / 2; gr = (r['groom_L'] + r['groom_R']) / 2
        rows.append((combo, gf, fd, gr, r['DNp04_L'], r['DNp04_R']))
    col = {'noescape': 1, 'escape': 1, 'strong': 1, 'oneside': 1, 'eat': 2, 'noeat': 2, 'feast': 2, 'groom': 3, 'nogroom': 3, 'eat_noescape': 2}[st['goal']]
    rows.sort(key=lambda x: x[col])
    for x in rows: print(f"  {x[0]:32s} GF {x[1]:6.1f} FD {x[2]:6.1f} GR {x[3]:6.1f}  P4 {x[4]:6.1f}/{x[5]:6.1f}")
