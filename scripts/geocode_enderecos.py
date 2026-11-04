"""Posiciona pelo endereço as escolas privadas que o Catálogo do INEP traz sem latitude e longitude.

Uso:  python3 scripts/geocode_enderecos.py SP
      (depois)  python3 scripts/build_uf.py SP <malha.gpkg> "São Paulo"  e  python3 scripts/make_platform.py

- Fonte: OpenStreetMap (Nominatim), dados ODbL, que permitem guardar o resultado.
  Respeita a política de uso: 1 consulta por segundo e identificação no User-Agent.
- Só consulta escolas com alunos em 2025 que hoje caem no centro do bairro ou do município (fonte 'b' ou 'm').
- Aceita só resultados no nível de rua ou de endereço, dentro do município e a menos de 2 km do centro do CEP de 5 dígitos
  da escola. O centro do CEP é a mediana das escolas do Catálogo que já têm coordenada nesse CEP (no SP, metade das
  escolas fica a menos de 0,4 km dele). Assim, uma rua de mesmo nome em outro bairro é descartada.
- O OpenStreetMap quase não tem CEPs do Brasil, então não consultamos por CEP. Se nada passar, usa o próprio centro do CEP (nivel 'cep_vizinhos', tratado como posição aproximada).
- Grava em dados/geocode_enderecos.csv (code,lat,lon,nivel,dist_cep_km). É incremental: rodar de novo continua de onde parou.
"""
import sys, os, re, json, time, csv, urllib.parse, urllib.request
import pandas as pd

UF = sys.argv[1]
OUT = 'dados/geocode_enderecos.csv'
UA = 'ReezuRaioXEscolar/1.0 (geocodificacao pontual de escolas privadas a partir do Catalogo do INEP)'
API = 'https://nominatim.openstreetmap.org/search?'

E = json.load(open(f'uf/{UF}/escolas.json'))
S = json.load(open(f'uf/{UF}/setores.json'))
muns = {int(k): v for k, v in S['muns'].items()}
box = {}
for r in S['s']:
    m, x, y = r[0], r[10], r[11]
    b = box.setdefault(m, [x, x, y, y])
    b[0] = min(b[0], x); b[1] = max(b[1], x); b[2] = min(b[2], y); b[3] = max(b[3], y)
PAD = 2 / 111  # ~2 km

cat = pd.concat([pd.read_csv(f, dtype=str, encoding='utf-8-sig') for f in sorted(__import__('glob').glob('dados/catalogo_privadas_*.csv'))])
cat = cat[cat.UF == UF].drop_duplicates('Código INEP').set_index('Código INEP')
cat['cep5'] = cat['Endereço'].str.extract(r'(\d{5})-?\d{3}')[0]
_la = pd.to_numeric(cat.Latitude.str.strip(), errors='coerce'); _lo = pd.to_numeric(cat.Longitude.str.strip(), errors='coerce')
ref = pd.DataFrame({'cep5': cat.cep5, 'lat': _la, 'lon': _lo}).dropna().groupby('cep5').agg(lat=('lat', 'median'), lon=('lon', 'median'))
def kmd(a, b, c, d): return ((a - c) ** 2 * 111.3 ** 2 + ((b - d) * 111.3 * 0.92) ** 2) ** .5
MAXKM = 2.0

done = set()
if os.path.exists(OUT):
    done = set(pd.read_csv(OUT, dtype=str).code)
else:
    with open(OUT, 'w', newline='') as f: csv.writer(f).writerow(['code', 'lat', 'lon', 'nivel', 'dist_cep_km'])

def parse(end):
    """'RUA X, 135 151. VILA VERA. 04295-030 São Paulo - SP.' -> (rua, numero, bairro, cep)"""
    end = (end or '').strip()
    cep = (re.search(r'(\d{5})-?(\d{3})', end) or [None])[0]
    head = end.split('.')[0]
    rua, _, resto = head.partition(',')
    num = (re.match(r'\s*(\d+)', resto) or [None, ''])[1]
    parts = [p.strip() for p in end.split('.') if p.strip()]
    bairro = parts[1] if len(parts) > 2 and not re.match(r'\d{5}', parts[1]) else ''
    return rua.strip().title(), num, bairro.title(), cep

last = [0.0]
def ask(params):
    wait = 1.1 - (time.time() - last[0])
    if wait > 0: time.sleep(wait)
    url = API + urllib.parse.urlencode({**params, 'format': 'jsonv2', 'limit': 3, 'countrycodes': 'br', 'addressdetails': 0})
    for tentativa in range(3):
        try:
            last[0] = time.time()
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=30) as r:
                return json.load(r)
        except Exception as e:
            time.sleep(5 * (tentativa + 1))
    return []

def inside(m, lat, lon):
    b = box.get(m)
    return b and b[0] - PAD <= lon <= b[1] + PAD and b[2] - PAD <= lat <= b[3] + PAD

alvo = [e for e in E if e[7][-1] > 0 and e[6] in ('b', 'm') and e[0] in cat.index and e[0] not in done]
# primeiro os municípios com mais escolas a posicionar (na capital, o centro do município empilharia centenas delas)
_n = __import__('collections').Counter(e[2] for e in alvo); alvo.sort(key=lambda e: (-_n[e[2]], e[0]))
print(UF, 'escolas a posicionar:', len(alvo), flush=True)
ok = 0
for i, e in enumerate(alvo, 1):
    code, m = e[0], e[2]; cidade = muns.get(m, '')
    rua, num, bairro, cep = parse(cat.loc[code, 'Endereço'])
    tentativas = []
    if rua: tentativas.append(('endereco', {'street': f'{num} {rua}'.strip(), 'city': cidade, 'state': UF, 'country': 'Brasil'}))
    if rua: tentativas.append(('rua', {'street': rua, 'city': cidade, 'state': UF, 'country': 'Brasil'}))
    c5 = cat.loc[code, 'cep5']; rc = ref.loc[c5] if isinstance(c5, str) and c5 in ref.index else None
    achou = None
    for nivel, p in tentativas:
        cands = []
        for res in ask(p):
            lat, lon, rank = float(res['lat']), float(res['lon']), int(res.get('place_rank', 0))
            if rank < 25 or not inside(m, lat, lon): continue  # 25 = CEP, 26+ = rua/endereço
            d = kmd(lat, lon, rc.lat, rc.lon) if rc is not None else None
            if d is None or d <= MAXKM: cands.append((d if d is not None else 0, lat, lon, d))
        if cands:
            _, lat, lon, d = min(cands); achou = (round(lat, 6), round(lon, 6), nivel, '' if d is None else round(d, 2)); break
    if not achou and rc is not None:
        achou = (round(rc.lat, 6), round(rc.lon, 6), 'cep_vizinhos', 0)
    with open(OUT, 'a', newline='') as f:
        w = csv.writer(f)
        w.writerow([code, *achou] if achou else [code, '', '', 'nao_encontrado', ''])
    ok += bool(achou)
    if i % 50 == 0 or i == len(alvo): print(f'{i}/{len(alvo)} posicionadas {ok}', flush=True)
