# Raio-X Escolar · Reezu

Plataforma da Reezu de análise de mercado escolar. Para qualquer escola privada, ela mostra:

- o histórico de matrículas de 2019 a 2025, por segmento;
- os concorrentes num raio de 3 km;
- as crianças por faixa de idade e a renda média no raio;
- um mapa de calor por setor censitário do IBGE.

Hoje ela tem Ceará e Amazonas. Cada estado novo precisa da malha de setores censitários do IBGE daquele estado (arquivo .gpkg).

## Estrutura

| Pasta | O que tem |
|---|---|
| `plataforma/` | O site pronto: `index.html` (HTML, CSS e JS num arquivo só) e `data/` com os JSON de cada estado (`{UF}_esc.json` com as escolas e `{UF}_setores.json` com os setores e os polígonos). |
| `scripts/build_uf.py` | Processa um estado. Lê a malha do IBGE (.gpkg), os agregados por setor (demografia e renda) e o Censo Escolar, e gera `uf/{UF}/setores.json`, `escolas.json` e `meta.json`. |
| `scripts/make_platform.py` | Junta todos os estados de `uf/` e gera `plataforma/index.html` e `plataforma/data/` a partir de `template/tool.html`. |
| `template/tool.html` | Modelo da interface usado pelo `make_platform.py`. |
| `uf/` | Estados já processados (CE, AM). |
| `dados/` | Bases: Censo Escolar de todas as escolas privadas do Brasil de 2019 a 2025 (`.parquet`), Catálogo de Escolas do INEP do Norte e Nordeste (latitude e longitude) e as coordenadas corrigidas à mão (`geocode_google.csv`). |
| `assets/` | Logotipo da Reezu em vetor, para fundo escuro e fundo claro. |
| `Manual-da-Marca-Reezu.pdf` | Manual da marca: cores, tipografia, grafismos e tom de voz. |
| `dados/ibge/` | Agregados por setores do Censo 2022 (demografia e renda do responsável, Brasil inteiro). |

Rode tudo a partir da raiz desta pasta.

## Como rodar

```bash
pip install pandas geopandas pyarrow numpy
python3 -m http.server 8765 --directory plataforma   # abra http://localhost:8765
```

O `index.html` busca os arquivos de `data/` sob demanda, então ele precisa de um servidor. Abrir com duplo clique não funciona.

## Como adicionar um estado

```bash
python3 scripts/build_uf.py PE caminho/PE_setores_CD2022.gpkg "Pernambuco"
python3 scripts/make_platform.py
```

Para estados do Sudeste, Sul e Centro-Oeste também é preciso exportar o Catálogo de Escolas do INEP dessas regiões. Ele traz a latitude e longitude das escolas. Junte esse arquivo com `dados/catalogo_privadas_N_NE.csv`.

## Regras de dados

- **Concorrentes:** contam só escolas com Infantil, Fundamental ou Médio regular. Unidades só técnicas ou só EJA ficam de fora.
- **Setores no raio:** um setor entra no raio pelo seu ponto representativo.
- **Faixas de idade por segmento:** são aproximações a partir das faixas do IBGE.
  - Infantil: 0–4 anos + 20% de 5–9 anos.
  - Fundamental I: 80% de 5–9 anos + 20% de 10–14 anos.
  - Fundamental II: 80% de 10–14 anos.
  - Médio: 60% de 15–19 anos.
- **Escolas sem coordenada no Catálogo:** são posicionadas no centro do bairro, ponderado pela população. O mapa marca essas escolas como posição aproximada.
- **Avaliações do Google Maps:** não entram nos arquivos, por causa dos termos de uso do Google.

## Ideias de próximos passos

- Hospedar com login (por exemplo Vercel ou Netlify com autenticação, ou o servidor da Hostinger).
- Exportar o Raio-X de uma escola em PDF.
- Integrar a Biblioteca de Anúncios da Meta pela API oficial.
