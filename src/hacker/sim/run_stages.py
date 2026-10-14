"""Run every allowed combination for every stage (seed 7), cached in runs.jsonl.
Usage: run_stages.py [extra seeds for verification: --verify verify.json]"""
import json, sys, os, time, itertools
from multiprocessing import Pool
from stages import STAGES
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, 'runs.jsonl')
def key(scen, sil, act, seed): return f"{scen}|{','.join(sorted(sil))}|{','.join(sorted(act))}|{seed}"
def job(k):
    from common import simulate, readout
    scen, sil, act, seed = k.split('|')
    sil = [x for x in sil.split(',') if x]; act = [x for x in act.split(',') if x]
    t = time.time(); c = simulate(scen, silence=sil, activate=act, seed=int(seed))
    return k, readout(c), round(time.time() - t, 1)
def stage_keys(st, seed=7):
    out = []
    for k in range(0, st['K'] + 1):
        for comb in itertools.combinations(st['cands'], k):
            sil, act = (comb, ()) if st['mode'] == 'sil' else ((), comb)
            out.append(key(st['scen'], sil, act, seed))
    return out
def load_cache():
    d = {}
    if os.path.exists(CACHE):
        for line in open(CACHE):
            r = json.loads(line); d[r['k']] = r
    return d
if __name__ == '__main__':
    import common  # load connectome once in parent, children fork
    keys = sys.argv[1:] if len(sys.argv) > 1 else None
    done = load_cache()
    if keys is None:
        keys = []
        for st in STAGES: keys += stage_keys(st)
    todo = [k for k in dict.fromkeys(keys) if k not in done]
    print(len(todo), 'runs to do', flush=True); t0 = time.time()
    with Pool(3) as p, open(CACHE, 'a') as f:
        for i, (k, r, sec) in enumerate(p.imap_unordered(job, todo)):
            f.write(json.dumps({'k': k, 'r': r, 'sec': sec}) + '\n'); f.flush()
            print(i, k, sec, flush=True)
    print('done', round(time.time() - t0))
