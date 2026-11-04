"""Dá nome aos setores que a malha do IBGE traz sem bairro.

Uso:  python3 scripts/nomear_bairros.py SP      (o build_uf.py já chama este script no fim)

Em muitos municípios (ex.: Cotia e Sorocaba, em SP) o IBGE não tem bairros oficiais, e o setor vem sem nome.
Sem nome, o mapa fica sem rótulos e o bloco "Onde crescer" não tem o que agrupar.
Aqui, cada setor sem nome recebe o bairro da escola privada mais próxima com posição confiável
(Catálogo do INEP, correção manual ou endereço conferido com o CEP), do mesmo município e a até 1,5 km.
O bairro da escola vem do Censo Escolar ou do endereço do Catálogo.
O setor ganha a marca de nome aproximado (13º campo = 1), que a página mostra.
Rodar de novo é seguro: os nomes aproximados anteriores são refeitos.
"""
import sys, json, math, collections

UF = sys.argv[1]
D = f'uf/{UF}'
MAXKM = 1.5

S = json.load(open(f'{D}/setores.json'))
E = json.load(open(f'{D}/escolas.json'))

def nome(b):
    b = (b or '').strip().strip('.').strip()
    return b if len(b) >= 3 and not b[:5].replace('-', '').isdigit() else ''

# escolas com posição confiável e bairro, por município
esc = collections.defaultdict(list)
for e in E:
    if e[4] is None or e[6] not in ('i', 'e', 'c'): continue
    b = nome(e[3])
    if b: esc[e[2]].append((e[4], e[5], b))

# grade de 0,02 grau para achar a escola mais próxima depressa
G = 0.02
grade = {m: collections.defaultdict(list) for m in esc}
for m, lst in esc.items():
    for la, lo, b in lst: grade[m][(math.floor(lo / G), math.floor(la / G))].append((la, lo, b))

n0 = n1 = 0
for r in S['s']:
    if len(r) > 13 and r[13] == 1: r[1] = ''; r.pop()  # refaz nomes aproximados anteriores
    if r[1]: continue
    n0 += 1
    m, x, y = r[0], r[10], r[11]
    if m not in grade: continue
    cx, cy = math.floor(x / G), math.floor(y / G); best = None
    for i in range(cx - 4, cx + 5):
        for j in range(cy - 4, cy + 5):
            for la, lo, b in grade[m].get((i, j), ()):
                d = math.hypot((la - y) * 111.32, (lo - x) * 111.32 * math.cos(y * math.pi / 180))
                if d <= MAXKM and (best is None or d < best[0]): best = (d, b)
    if best:
        r[1] = best[1]
        while len(r) < 13: r.append(None)
        r.append(1); n1 += 1

json.dump(S, open(f'{D}/setores.json', 'w'), separators=(',', ':'), ensure_ascii=False)
print(UF, 'setores sem bairro na malha:', n0, '| nomeados pela escola mais próxima:', n1, '| seguem sem nome:', n0 - n1)
