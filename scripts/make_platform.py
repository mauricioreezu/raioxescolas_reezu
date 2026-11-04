"""Junta os estados de uf/ e gera plataforma/index.html e plataforma/data/ a partir de template/tool.html.

O template já é multi-estado. Este script só:
- grava os JSON de cada estado em plataforma/data/. Estados grandes (mapa acima de 8 MB, como SP) têm os setores
  divididos em quadrados de 0,4 grau; os quadrados com mais de 1 MB (capital) viram quadrados de 0,1 grau
  (data/{UF}_s/b_i_j.json e s_i_j.json). A página baixa só os quadrados em volta da escola;
- injeta a lista de estados (__STATES__);
- embute os logotipos oficiais de assets/ (__LOGO_DARK__, __LOGO_LIGHT__) como data URI, sem alterar o desenho.
"""
import json, os, glob, base64, re, math, shutil, collections

P = 'plataforma'
SPLIT_MB = 8      # acima disso, o mapa do estado é dividido em quadrados
TILE = 0.4        # quadrado base, em graus (~44 km)
SUB = 0.1         # quadrado menor, para os quadrados base acima de SUB_MB
SUB_MB = 1.0
os.makedirs(P + '/data', exist_ok=True)

states = []
for d in sorted(glob.glob('uf/*/meta.json')):
    m = json.load(open(d)); uf = m['uf']; D = os.path.dirname(d)
    S = json.load(open(D + '/setores.json')); E = json.load(open(D + '/escolas.json'))
    json.dump({'muns': S['muns'], 'e': E}, open(f'{P}/data/{uf}_esc.json', 'w'), separators=(',', ':'), ensure_ascii=False)
    st = {'uf': uf, 'nome': m['nome'], 'bbox': m['bbox'], 'n': m['n']}
    full = f'{P}/data/{uf}_setores.json'; tdir = f'{P}/data/{uf}_s'
    if os.path.exists(tdir): shutil.rmtree(tdir)
    if os.path.getsize(D + '/setores.json') > SPLIT_MB * 1e6:
        if os.path.exists(full): os.remove(full)
        os.makedirs(tdir)
        key = lambda r, T: f'{math.floor(r[10] / T)}_{math.floor(r[11] / T)}'  # pelo ponto representativo, o mesmo que decide o raio
        base = collections.defaultdict(list)
        for r in S['s']: base[key(r, TILE)].append(r)
        tiles = {}
        for k, rs in base.items():
            if len(json.dumps(rs, separators=(',', ':'), ensure_ascii=False).encode()) > SUB_MB * 1e6:
                for r in rs: tiles.setdefault('s_' + key(r, SUB), []).append(r)
            else: tiles['b_' + k] = rs
        for k, rs in tiles.items():
            json.dump({'s': rs}, open(f'{tdir}/{k}.json', 'w'), separators=(',', ':'), ensure_ascii=False)
        st['tile'] = TILE; st['sub'] = SUB; st['tiles'] = sorted(tiles)
        big = max(os.path.getsize(f'{tdir}/{k}.json') for k in tiles)
        print(uf, 'setores em', len(tiles), 'quadrados; maior', round(big / 1e6, 2), 'MB')
    else:
        json.dump({'s': S['s']}, open(full, 'w'), separators=(',', ':'), ensure_ascii=False)
    states.append(st)

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
for f in sorted(os.listdir(P + '/data')):
    if f.endswith('.json'): print(f, round(os.path.getsize(P + '/data/' + f) / 1e6, 2), 'MB')
print('index', round(len(t) / 1e3), 'KB')
