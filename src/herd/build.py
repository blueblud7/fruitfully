"""app.html + ../../fly-escape/brain_tables.json(빛·루밍·냄새 반응표) → index.html (Artifact용), local.html (로컬 확인용)"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', '..', 'fly-escape', 'brain_tables.json')
CDN = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js'

t = json.load(open(SRC, encoding='utf-8'))
def r(tb):  # 발화율은 0.01Hz로 반올림 (크기 줄이기)
    return {k: {n: round(v, 2) for n, v in row.items()} for k, row in tb.items()}
data = {'levels2d': t['levels2d'], 'readouts': t['readouts'], 'light': r(t['light']), 'loom': r(t['loom']),
        'odor': r(t['odor']), 'odor_levels': t['odor_levels'], 'meta': t['meta']}
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
