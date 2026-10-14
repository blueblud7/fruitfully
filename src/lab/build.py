"""app.html + brain_tables.json + brain_extra.json → index.html (artifact) + local.html (offline)

brain_extra.json is slimmed faithfully:
  - firing-rate tables rounded to 0.1 Hz
  - neuron positions: FlyWire voxel coords (4×4×40 nm) → z ×10 for isotropy, centred,
    uniformly scaled so the half-width is 1000, rounded to integers (≈0.4 µm resolution)
  - wave neuron ids → indices into the neuron list; first-spike times rounded to 0.1 ms
"""
import json

t = json.load(open('brain_tables.json'))
t['odor'] = {('%g' % float(k)): v for k, v in t['odor'].items()}  # match JS String(number)
t['odor_levels'] = [float('%g' % x) for x in t['odor_levels']]

e = json.load(open('brain_extra.json'))
r1 = lambda tb: {k: {a: round(b, 1) for a, b in v.items()} for k, v in tb.items()}
nb = e['neurons']
xs, ys, zs = nb['x'], nb['y'], [z * 10 for z in nb['z']]   # 40 nm sections vs 4 nm pixels
cx, cy, cz = [(min(a) + max(a)) / 2 for a in (xs, ys, zs)]
s = 1000 / ((max(xs) - min(xs)) / 2)
pos = []
for x, y, z in zip(xs, ys, zs):
    pos += [round((x - cx) * s), round((y - cy) * s), round((z - cz) * s)]
types = sorted(set(nb['type']), key=lambda x: (x is None, x or ''))
tix = {ty: k for k, ty in enumerate(types)}
local = {fid: k for k, fid in enumerate(nb['i'])}
waves = {}
for name, w in e['waves'].items():
    waves[name] = {'i': [local[i] for i in w['idx']], 't': [round(x, 1) for x in w['t']],
                   'n': w['n'], 's': [local[i] for i in w['stim']]}
X = {
    'levels': e['levels'], 'readouts': e['readouts'], 'counts': e['counts'], 'classes': e['classes'],
    'taste': r1(e['taste']), 'water': r1(e['water']), 'groom': r1(e['groom']),
    'silence': {k: r1(v) for k, v in e['silence'].items()},
    'nb': {'p': pos, 'c': nb['cls'], 'ty': [tix[x] for x in nb['type']], 'types': [x or '' for x in types]},
    'waves': waves,
}

s = open('app.html', encoding='utf-8').read()
assert '/*TABLES*/null' in s and '/*EXTRA*/null' in s
s = s.replace('/*TABLES*/null', json.dumps(t, separators=(',', ':')))
s = s.replace('/*EXTRA*/null', json.dumps(X, separators=(',', ':'), ensure_ascii=False))
open('index.html', 'w', encoding='utf-8').write(s)

loc = ('<!doctype html>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width,initial-scale=1">\n' + s)
loc = loc.replace('https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js', 'vendor/three.min.js')
loc = loc.replace('https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js', 'vendor/OrbitControls.js')
assert 'vendor/three.min.js' in loc and 'vendor/OrbitControls.js' in loc
open('local.html', 'w', encoding='utf-8').write(loc)
print('index.html %d bytes, local.html %d bytes' % (len(s.encode()), len(loc.encode())))
