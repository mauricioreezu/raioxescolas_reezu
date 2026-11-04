import sys, json, os, unicodedata, numpy as np, pandas as pd, geopandas as gpd
UF, GPKG, NOME = sys.argv[1], sys.argv[2], sys.argv[3]
OUT=f'uf/{UF}'; os.makedirs(OUT,exist_ok=True)
def norm(s): return unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().upper().strip() if isinstance(s,str) else ''
# ---------- setores ----------
s=gpd.read_file(GPKG)
# a malha "com atributos" traz v0001 (moradores) e v0007 (domicílios); a malha simples não traz, e aí usamos os agregados (abaixo)
for c in ('v0001','v0007'):
    if c not in s.columns: s[c]=np.nan
# sem bairro (ex.: capital paulista), usa o distrito quando ele não é o próprio município
if 'NM_DIST' in s.columns:
    d=s.NM_DIST.where(s.NM_DIST.notna()&(s.NM_DIST!=s.NM_MUN))
    s['NM_BAIRRO']=s.NM_BAIRRO.where(s.NM_BAIRRO.notna()&(s.NM_BAIRRO.astype(str).str.strip()!=''),d)
s=s[['CD_SETOR','CD_MUN','NM_MUN','NM_BAIRRO','v0001','v0007','geometry']].drop_duplicates('CD_SETOR')
cuf=s.CD_SETOR.iloc[0][:2]
s=s.to_crs(5880); s['ha']=s.area/1e4; s=s.to_crs(4326)
dem=pd.read_csv('dados/ibge/Agregados_por_setores_demografia_BR.csv',sep=';',dtype=str,encoding='latin1')
dem=dem[dem.CD_setor.str.startswith(cuf)].drop_duplicates('CD_setor').set_index('CD_setor')
tot=pd.to_numeric(dem.V01006,errors='coerce'); A=dem[['V010%d'%i for i in range(31,42)]].apply(pd.to_numeric,errors='coerce')
rest=(tot-A.sum(axis=1)).clip(lower=0); nx=A.isna().sum(axis=1); A=A.apply(lambda c:c.fillna(rest/nx.replace(0,np.nan))).fillna(0)
ren=pd.read_csv('dados/ibge/Agregados_por_setores_renda_responsavel_BR.csv',sep=';',dtype=str).set_index('CD_SETOR')
ren=ren[ren.index.str.startswith(cuf)]; ren=ren[~ren.index.duplicated()]
s=s.set_index('CD_SETOR'); A4=A.iloc[:,:4].reindex(s.index).fillna(0)
s['renda']=pd.to_numeric(ren.V06004,errors='coerce').reindex(s.index)
s['pop']=pd.to_numeric(s.v0001,errors='coerce').fillna(tot.reindex(s.index)).fillna(0)
s['dom']=pd.to_numeric(s.v0007,errors='coerce').fillna(pd.to_numeric(ren.V06001,errors='coerce').reindex(s.index)).fillna(0)
s['geometry']=[g.simplify(0.00012 if ha<300 else (0.0008 if ha<5000 else 0.004),preserve_topology=True) for g,ha in zip(s.geometry,s.ha)]; s=gpd.GeoDataFrame(s,geometry='geometry',crs=4326); rp=s.geometry.representative_point()
muns={}; recs=[]
for cd,r in s.iterrows():
    g=r.geometry; polys=[g] if g.geom_type=='Polygon' else list(g.geoms); enc=[]
    for p in polys:
        co=np.round(np.array(p.exterior.coords)*1e5).astype(int); enc.append(np.diff(co,axis=0,prepend=[[0,0]]).flatten().tolist())
    a=A4.loc[cd].values
    recs.append([int(r.CD_MUN),r.NM_BAIRRO if isinstance(r.NM_BAIRRO,str) else '',int(r['pop']),int(r.dom),*[round(float(x),1) for x in a],
        None if pd.isna(r.renda) else int(round(r.renda)),round(float(r.ha),2),round(rp.loc[cd].x,5),round(rp.loc[cd].y,5),enc])
    muns[int(r.CD_MUN)]=r.NM_MUN
json.dump({'muns':muns,'s':recs},open(f'{OUT}/setores.json','w'),separators=(',',':'),ensure_ascii=False)
# ---------- escolas ----------
st=pd.DataFrame([[r[0],r[1],r[2],r[10],r[11]] for r in recs],columns=['mun','bairro','pop','x','y']); st['w']=st['pop']+1
def wc(g): return pd.Series({'x':(g.x*g.w).sum()/g.w.sum(),'y':(g.y*g.w).sum()/g.w.sum(),'x0':g.x.min(),'x1':g.x.max(),'y0':g.y.min(),'y1':g.y.max()})
mc=st.groupby('mun')[['x','y','w']].apply(wc); st['nb']=st.bairro.map(norm); bc=st[st.nb!=''].groupby(['mun','nb'])[['x','y','w']].apply(wc)
h=pd.read_parquet('dados/censo_privadas_BR_2019_2025.parquet'); h=h[h.SG_UF==UF].copy()
num=['QT_MAT_INF','QT_MAT_FUND_AI','QT_MAT_FUND_AF','QT_MAT_MED','QT_MAT_BAS']
for c in num: h[c]=pd.to_numeric(h[c],errors='coerce').fillna(0).astype(int)
h=h.sort_values('NU_ANO_CENSO')
import glob
cat=pd.concat([pd.read_csv(f,dtype=str,encoding='utf-8-sig') for f in sorted(glob.glob('dados/catalogo_privadas_*.csv'))]); cat=cat[cat.UF==UF].drop_duplicates('Código INEP').set_index('Código INEP')
geo=pd.read_csv('dados/geocode_google.csv',dtype={'code':str}).set_index('code')
# posições pelo endereço (scripts/geocode_enderecos.py, OpenStreetMap)
gend=pd.read_csv('dados/geocode_enderecos.csv',dtype={'code':str}) if os.path.exists('dados/geocode_enderecos.csv') else pd.DataFrame(columns=['code','lat','lon'])
gend=gend.dropna(subset=['lat','lon']).drop_duplicates('code',keep='last').set_index('code')
yrs=[str(y) for y in range(2019,2026)]; out=[]; fc={}
for code,g in h.groupby('CO_ENTIDADE'):
    last=g.iloc[-1]; mun=int(last.CO_MUNICIPIO)
    serie=[int(g[g.NU_ANO_CENSO==y].QT_MAT_BAS.sum()) if (g.NU_ANO_CENSO==y).any() else -1 for y in yrs]
    seg=[int(g[g.NU_ANO_CENSO=='2025'][c].sum()) for c in num[:4]] if (g.NU_ANO_CENSO=='2025').any() else [0,0,0,0]
    bairro=g.NO_BAIRRO.dropna().iloc[-1] if g.NO_BAIRRO.notna().any() else ''
    end='';lat=lon=np.nan;f=''
    if code in geo.index: lat,lon,f=geo.loc[code,'lat'],geo.loc[code,'lon'],'e'
    elif code in cat.index:
        la=pd.to_numeric(cat.loc[code,'Latitude'],errors='coerce'); lo=pd.to_numeric(cat.loc[code,'Longitude'],errors='coerce')
        if pd.notna(la) and mun in mc.index:
            m=mc.loc[mun]
            if m.x0-0.05<=lo<=m.x1+0.05 and m.y0-0.05<=la<=m.y1+0.05: lat,lon,f=la,lo,'i'
    # 'c' = endereço conferido com o CEP; 'p' = centro do CEP (aproximada)
    if not f and code in gend.index: lat,lon,f=float(gend.loc[code,'lat']),float(gend.loc[code,'lon']),('p' if gend.loc[code,'nivel']=='cep_vizinhos' else 'c')
    if code in cat.index:
        end=cat.loc[code,'Endereço']
        if not bairro:
            parts=[p.strip() for p in end.split('.') if p.strip()]; sg=[p for p in parts if not p[:5].replace('-','').isdigit()]; bairro=sg[-1] if sg else ''
    if not f:
        nb=norm(bairro)
        if (mun,nb) in bc.index: b=bc.loc[(mun,nb)]; lat,lon,f=b.y,b.x,'b'
        elif mun in mc.index: m=mc.loc[mun]; lat,lon,f=m.y,m.x,'m'
    fc[f]=fc.get(f,0)+1
    out.append([code,last.NO_ENTIDADE.title(),mun,bairro.title() if isinstance(bairro,str) else '',round(float(lat),5) if pd.notna(lat) else None,round(float(lon),5) if pd.notna(lon) else None,f,serie,seg,(end or '').strip()])
json.dump(out,open(f'{OUT}/escolas.json','w'),separators=(',',':'),ensure_ascii=False)
act=[o for o in out if o[7][-1]>0]
top=max(act,key=lambda o:o[7][-1])
bb=[float(st.x.min()),float(st.x.max()),float(st.y.min()),float(st.y.max())]
json.dump({'uf':UF,'nome':NOME,'top':top[0],'bbox':bb,'n':len(act),'fontes':{k:sum(1 for o in act if o[6]==k) for k in 'iecpbm'}},open(f'{OUT}/meta.json','w'))
print(UF,'setores',len(recs),round(os.path.getsize(f'{OUT}/setores.json')/1e6,2),'MB','| escolas',len(out),'ativas',len(act),{k:sum(1 for o in act if o[6]==k) for k in 'iecpbm'},'| maior',top[1],top[7][-1])
