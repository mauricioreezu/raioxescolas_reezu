"""Junta os estados de uf/ e gera plataforma/index.html e plataforma/data/ a partir de template/tool.html.

O template já é multi-estado. Este script só:
- grava os JSON de cada estado em plataforma/data/;
- injeta a lista de estados (__STATES__);
- embute os logotipos oficiais de assets/ (__LOGO_DARK__, __LOGO_LIGHT__) como data URI, sem alterar o desenho.
"""
import json, os, glob, base64, re

P = 'plataforma'
os.makedirs(P + '/data', exist_ok=True)

states = []
for d in sorted(glob.glob('uf/*/meta.json')):
    m = json.load(open(d)); uf = m['uf']; D = os.path.dirname(d)
    S = json.load(open(D + '/setores.json')); E = json.load(open(D + '/escolas.json'))
    json.dump({'muns': S['muns'], 'e': E}, open(f'{P}/data/{uf}_esc.json', 'w'), separators=(',', ':'), ensure_ascii=False)
    json.dump({'s': S['s']}, open(f'{P}/data/{uf}_setores.json', 'w'), separators=(',', ':'), ensure_ascii=False)
    states.append({'uf': uf, 'nome': m['nome'], 'bbox': m['bbox'], 'n': m['n']})

def svg_uri(path):
    return 'data:image/svg+xml;base64,' + base64.b64encode(open(path, 'rb').read()).decode()

t = open('template/tool.html', encoding='utf-8').read()
def rep(a, b):
    global t
    assert a in t, 'marcador ausente no template: ' + a
    t = t.replace(a, b)

rep('__STATES__', json.dumps(states, ensure_ascii=False))
rep('__LOGO_DARK__', svg_uri('assets/logo-reezu-fundo-escuro.svg'))
rep('__LOGO_LIGHT__', svg_uri('assets/logo-reezu-fundo-claro.svg'))

# tom de voz da marca: estas palavras não podem aparecer na interface
for w in ('lead', 'funil', 'alavanc', 'urgente'):
    assert not re.search(r'\b' + w, t, re.I), 'palavra fora do tom da marca: ' + w

open(P + '/index.html', 'w', encoding='utf-8').write(t)
json.dump(states, open(P + '/states.json', 'w'), ensure_ascii=False)
for f in sorted(os.listdir(P + '/data')): print(f, round(os.path.getsize(P + '/data/' + f) / 1e6, 2), 'MB')
print('index', round(len(t) / 1e3), 'KB')
