# Raio-X Escolar · Reezu

Plataforma da Reezu de análise de mercado escolar. Para qualquer escola privada, ela mostra:

- o histórico de matrículas de 2019 a 2025, por segmento;
- os concorrentes num raio de 3 km;
- as crianças por faixa de idade e a renda média no raio;
- um mapa de calor de oportunidade por setor censitário do IBGE e os 3 bairros com mais oportunidade ("Onde crescer").

Hoje ela tem Ceará, Amazonas e São Paulo. Cada estado novo precisa da malha de setores censitários do IBGE daquele estado (arquivo .gpkg).

## Estrutura

| Pasta | O que tem |
|---|---|
| `plataforma/` | O site pronto: `index.html` (HTML, CSS e JS num arquivo só) e `data/` com os JSON de cada estado (`{UF}_esc.json` com as escolas e `{UF}_setores.json` com os setores e os polígonos). |
| `scripts/build_uf.py` | Processa um estado. Lê a malha do IBGE (.gpkg), os agregados por setor (demografia e renda) e o Censo Escolar, e gera `uf/{UF}/setores.json`, `escolas.json` e `meta.json`. |
| `scripts/make_platform.py` | Junta todos os estados de `uf/` e gera `plataforma/index.html` e `plataforma/data/` a partir de `template/tool.html`. Injeta a lista de estados e embute os logotipos de `assets/`. Para se o template tiver "lead", "funil", "alavancar" ou "urgente". |
| `template/tool.html` | Interface (multi-estado) com a identidade visual do Manual da Marca. Toda mudança visual é feita aqui e depois `python3 scripts/make_platform.py`. Não edite `plataforma/index.html` à mão. |
| `scripts/geocode_enderecos.py` | Localiza pelo endereço (OpenStreetMap) as escolas que o Catálogo traz sem coordenada, conferindo com o CEP. Grava `dados/geocode_enderecos.csv`, que o `build_uf.py` lê. |
| `uf/` | Estados já processados (CE, AM, SP). |
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
python3 scripts/geocode_enderecos.py PE      # opcional: localiza pelo endereço as escolas sem coordenada (~1 escola por segundo)
python3 scripts/build_uf.py PE caminho/PE_setores_CD2022.gpkg "Pernambuco"   # de novo, para usar as posições novas
python3 scripts/make_platform.py
```

A malha está no IBGE em `geoftp.ibge.gov.br` (.../malhas_de_setores_censitarios__divisoes_intramunicipais/censo_2022/setores/gpkg/UF/{UF}/). Serve a malha simples: se ela não trouxer população (`v0001`) e domicílios (`v0007`), o script usa os agregados de `dados/ibge/`. Onde a malha não tem nome de bairro (ex.: capital paulista), o script usa o nome do distrito.

Estados com mapa acima de 8 MB (SP) são divididos pelo `make_platform.py` em quadrados de 0,1 grau (`data/{UF}_s/`), e a página só baixa os quadrados em volta da escola analisada.

O `build_uf.py` lê todos os arquivos `dados/catalogo_privadas_*.csv` (Catálogo de Escolas do INEP, com latitude e longitude). Já estão lá Norte e Nordeste (`_N_NE`) e São Paulo (`_SP`). Para outro estado do Sudeste, Sul ou Centro-Oeste, exporte o catálogo das escolas privadas dele e salve como `dados/catalogo_privadas_{UF}.csv`.

## Regras de dados

- **Concorrentes:** contam só escolas com Infantil, Fundamental ou Médio regular. Unidades só técnicas ou só EJA ficam de fora.
- **Setores no raio:** um setor entra no raio pelo seu ponto representativo.
- **Faixas de idade por segmento:** são aproximações a partir das faixas do IBGE.
  - Infantil: 0–4 anos + 20% de 5–9 anos.
  - Fundamental I: 80% de 5–9 anos + 20% de 10–14 anos.
  - Fundamental II: 80% de 10–14 anos.
  - Médio: 60% de 15–19 anos.
- **Escolas sem coordenada no Catálogo:** primeiro são localizadas pelo endereço (OpenStreetMap), aceitando só resultados a menos de 2 km do centro do CEP de 5 dígitos (mediana das escolas do Catálogo com coordenada naquele CEP). Sem isso, vão para o centro do CEP, ou do bairro ponderado pela população, ou do município. O mapa marca essas três últimas como posição aproximada (≈).
- **Avaliações do Google Maps:** não entram nos arquivos, por causa dos termos de uso do Google.

## Índice de oportunidade (camada padrão do mapa)

Calculado no navegador para cada setor, a partir dos dados que já estão em `plataforma/data/`.

1. **Demanda (D):** crianças do setor nos segmentos que a escola oferece em 2025 (faixas de idade acima). Na análise por ponto, todos os segmentos. O seletor "Idade" do mapa restringe a um segmento.
2. **Demanda qualificada (Dq):** D se a renda média do responsável for maior ou igual ao mínimo escolhido (padrão 2 SM de 2022, R$ 2.424; ajustável de 1 a 5 SM). Senão, 0. Setor sem renda divulgada fica "sem dado" (cinza).
3. **Pressão (P):** soma dos alunos de 2025, nos mesmos segmentos, das concorrentes a menos de 1 km do ponto representativo do setor, cada uma com peso `1 − distância em km`. Vale a mesma regra de concorrente (só regulares) e a escola analisada fica de fora.
4. **Índice:** `Dq ÷ (1 + P ÷ P̄)`, em que P̄ é a pressão média dos setores do raio. Normalizado de 0 a 100 dentro do raio (100 = melhor setor do raio).
5. **Cores:** 5 faixas por quintis dos setores do raio com índice maior que zero (#FFF3C4, #FDD27A, #F9A23F, #E8642C, #B8231F). Índice 0 cai na faixa mais fria.
6. **Onde crescer:** soma de `Dq ÷ (1 + P ÷ P̄)` dos setores de cada bairro dentro do raio; os 3 maiores aparecem abaixo do mapa.

## Ideias de próximos passos

- Hospedar com login (por exemplo Vercel ou Netlify com autenticação, ou o servidor da Hostinger).
- Exportar o Raio-X de uma escola em PDF.
- Integrar a Biblioteca de Anúncios da Meta pela API oficial.
