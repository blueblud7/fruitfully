"""Pick keys to re-run on seeds 8,9,10: baseline, every solution (max 4 smallest), and the
closest non-solution (near miss). Prints the keys; feed them to run_stages.py."""
import sys
from stages import STAGES
from run_stages import load_cache, stage_keys, key
sys.argv = sys.argv[:1]
import importlib
from texts import TH, PARAM
C = load_cache()
def rk(r):
    g = (r['GF_L'] + r['GF_R']) / 2; f = (r['feed_L'] + r['feed_R']) / 2; m = (r['groom_L'] + r['groom_R']) / 2
    return g, f, m, r['DNp04_L'], r['DNp04_R']
def ok(goal, r, p):
    g, f, m, a, b = rk(r)
    return {'noescape': g <= TH['GF'], 'escape': g > TH['GF'], 'eat': f >= TH['FEED'], 'noeat': f < TH['FEED'],
            'groom': m >= TH['GROOM'], 'nogroom': m < TH['GROOM'], 'feast': f >= (p or 0), 'strong': g >= (p or 0),
            'oneside': g > TH['GF'] and max(a, b) > 0 and min(a, b) <= (p or 0) * max(a, b),
            'eat_noescape': f >= TH['FEED'] and g <= TH['GF']}[goal]
def margin(goal, r, p):
    g, f, m, a, b = rk(r)
    return {'noescape': TH['GF'] - g, 'escape': g - TH['GF'], 'eat': f - TH['FEED'], 'noeat': TH['FEED'] - f,
            'groom': m - TH['GROOM'], 'nogroom': TH['GROOM'] - m, 'feast': f - (p or 0), 'strong': g - (p or 0),
            'oneside': ((p or 0) * max(a, b) - min(a, b)) if g > TH['GF'] else -999,
            'eat_noescape': min(f - TH['FEED'], TH['GF'] - g)}[goal]
out = []
for st in STAGES:
    p = PARAM.get(st['id']); ks = [k for k in stage_keys(st) if k in C]
    sols = sorted([k for k in ks if ok(st['goal'], C[k]['r'], p) and k != stage_keys(st)[0]], key=lambda k: (k.count(','), -margin(st['goal'], C[k]['r'], p)))[:4]
    non = sorted([k for k in ks if not ok(st['goal'], C[k]['r'], p)], key=lambda k: -margin(st['goal'], C[k]['r'], p))[:1]
    for k in [stage_keys(st)[0]] + sols + non:
        for sd in (8, 9, 10): out.append(k.rsplit('|', 1)[0] + f'|{sd}')
print(' '.join(dict.fromkeys(out)))
