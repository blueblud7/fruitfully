"""app.html + brain_extra.json(맛·물·그루밍 반응표만) → index.html (Artifact용), local.html (로컬 확인용)"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', '..', 'fly-escape', 'brain_extra.json')
CDN = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js'

e = json.load(open(SRC, encoding='utf-8'))
r1 = lambda v: round(v, 2)
data = {
    'levels': e['levels'],
    'taste': {k: {n: r1(x) for n, x in v.items()} for k, v in e['taste'].items()},
    'water': {k: {n: r1(x) for n, x in v.items()} for k, v in e['water'].items()},
    'groom': {k: {n: r1(x) for n, x in v.items()} for k, v in e['groom'].items()},
    'readouts': {'taste': e['readouts']['taste'], 'groom': e['readouts']['groom']},
    'counts': {k: e['counts'][k] for k in ('sugar', 'bitter', 'water', 'antenna_bristle', 'JO_CE')},
}
s = open(os.path.join(HERE, 'app.html'), encoding='utf-8').read()
assert s.count('/*DATA*/null') == 1, 'placeholder missing'
out = s.replace('/*DATA*/null', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
low = out.lower()
for tag in ('<!doctype', '<html', '<head', '<body'):
    assert tag not in low, tag
assert out.lstrip().startswith('<title>')
assert CDN in out
open(os.path.join(HERE, 'index.html'), 'w', encoding='utf-8').write(out)

local = ('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
         + out.replace(CDN, 'vendor/three.min.js'))
open(os.path.join(HERE, 'local.html'), 'w', encoding='utf-8').write(local)
print('built index.html (%d bytes), local.html (%d bytes)' % (len(out.encode()), len(local.encode())))
