"""app.html + brain_tables.json(루밍 반응표만) → index.html (Artifact용), local.html (로컬 확인용)"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'fly-escape', 'brain_tables.json')
CDN = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js'

t = json.load(open(SRC, encoding='utf-8'))
loom = {'levels2d': t['levels2d'], 'loom': t['loom'], 'meta': t['meta']}
s = open(os.path.join(HERE, 'app.html'), encoding='utf-8').read()
assert s.count('/*LOOM*/null') == 1, 'placeholder missing'
out = s.replace('/*LOOM*/null', json.dumps(loom, ensure_ascii=False, separators=(',', ':')))
low = out.lower()
for tag in ('<!doctype', '<html', '<head', '<body'):
    assert tag not in low, tag
assert out.lstrip().startswith('<title>')
open(os.path.join(HERE, 'index.html'), 'w', encoding='utf-8').write(out)

assert CDN in out
local = ('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
         + out.replace(CDN, 'vendor/three.min.js'))
open(os.path.join(HERE, 'local.html'), 'w', encoding='utf-8').write(local)
print('built index.html (%d bytes), local.html (%d bytes)' % (len(out.encode()), len(local.encode())))
