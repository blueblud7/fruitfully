"""app.html + hacker_data.json → index.html (Artifact, no doctype/html/head/body) + local.html (offline, vendor/)"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
CDN3 = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js'
CDNO = 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js'
d = json.load(open(os.path.join(HERE, 'hacker_data.json'), encoding='utf-8'))
s = open(os.path.join(HERE, 'app.html'), encoding='utf-8').read()
assert s.count('/*DATA*/null') == 1, 'placeholder missing'
out = s.replace('/*DATA*/null', json.dumps(d, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'))
low = out.lower()
for tag in ('<!doctype', '<html', '<head', '<body'):
    assert tag not in low, tag
assert out.lstrip().startswith('<title>') and CDN3 in out and CDNO in out
open(os.path.join(HERE, 'index.html'), 'w', encoding='utf-8').write(out)
loc = ('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
       + out.replace(CDN3, 'vendor/three.min.js').replace(CDNO, 'vendor/OrbitControls.js'))
open(os.path.join(HERE, 'local.html'), 'w', encoding='utf-8').write(loc)
n = len(out.encode()); assert n < 3_000_000, n
print('index.html %d bytes, local.html %d bytes' % (n, len(loc.encode())))
