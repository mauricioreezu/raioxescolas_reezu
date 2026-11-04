import json, os, glob
P='plataforma'; os.makedirs(P+'/data',exist_ok=True)
NOMES={'AC':'Acre','AL':'Alagoas','AP':'Amapá','AM':'Amazonas','BA':'Bahia','CE':'Ceará','DF':'Distrito Federal','ES':'Espírito Santo','GO':'Goiás','MA':'Maranhão','MT':'Mato Grosso','MS':'Mato Grosso do Sul','MG':'Minas Gerais','PA':'Pará','PB':'Paraíba','PR':'Paraná','PE':'Pernambuco','PI':'Piauí','RJ':'Rio de Janeiro','RN':'Rio Grande do Norte','RS':'Rio Grande do Sul','RO':'Rondônia','RR':'Roraima','SC':'Santa Catarina','SP':'São Paulo','SE':'Sergipe','TO':'Tocantins'}
states=[]
for d in sorted(glob.glob('uf/*/meta.json')):
    m=json.load(open(d)); uf=m['uf']; D=os.path.dirname(d)
    S=json.load(open(D+'/setores.json')); E=json.load(open(D+'/escolas.json'))
    json.dump({'muns':S['muns'],'e':E},open(f'{P}/data/{uf}_esc.json','w'),separators=(',',':'),ensure_ascii=False)
    json.dump({'s':S['s']},open(f'{P}/data/{uf}_setores.json','w'),separators=(',',':'),ensure_ascii=False)
    states.append({'uf':uf,'nome':m['nome'],'bbox':m['bbox'],'n':m['n']})
t=open('template/tool.html').read()
def rep(a,b):
    global t; assert a in t,a[:80]; t=t.replace(a,b)
rep('<title>Raio-X Escolar Ceará</title>','<title>Raio-X Escolar</title>')
rep('Raio-X de mercado escolar · Ceará','Raio-X de mercado escolar')
rep('<label for="q">Busque uma escola privada do Ceará pelo nome, município ou código INEP</label>','<label for="q">Busque uma escola privada pelo nome, município, estado ou código INEP</label>\n      <div class="ufs" id="ufs"></div>')
rep('placeholder="Ex.: Conexão Saber, Lira Coutinho, Juazeiro do Norte, 23212020"','placeholder="Ex.: Conexão Saber, La Salle Manaus, Juazeiro do Norte"')
rep('escolas privadas do Ceará. A posição','escolas privadas. A posição')
rep('.err{color:var(--down);font-size:14px}','.err{color:var(--down);font-size:14px}\n.ufs{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:14px;color:var(--muted);align-items:center}\n.ufs b{color:var(--ink);font-weight:600}\n.ufs .soon{opacity:.75}\n.loading{position:fixed;left:50%;bottom:max(20px,env(safe-area-inset-bottom,0px));transform:translateX(-50%);background:var(--ink);color:var(--paper);padding:10px 16px;border-radius:999px;font-size:14px;z-index:50}')
rep('<script>window.SET=__SET__;window.ESC=__ESC__;</script>','<div class="loading" id="loading" hidden></div>\n<script>window.STATES='+json.dumps(states,ensure_ascii=False)+';</script>')
old_data=t[t.index('const MUN=SET.muns;'):t.index("const trendCol=")]
rep(old_data,'''const MUN={};const ES=[];const ESmap={};const SSC={};const UFN={};STATES.forEach(s=>UFN[s.uf]=s.nome);
const loading=document.getElementById('loading');
function showL(m){loading.textContent=m;loading.hidden=!m}
function addEsc(uf,d){Object.assign(MUN,d.muns);d.e.forEach(r=>{const s=r[7],t=s[6]>0?s[6]:0,mn=d.muns[r[2]]||'';const e={uf,code:r[0],nome:r[1],mun:r[2],mn,bairro:r[3],lat:r[4],lon:r[5],fonte:r[6],serie:s,seg:r[8],end:r[9],tot:t,
  v22:s[3]>0&&s[6]>=0?s[6]/s[3]-1:null,key:norm(r[1]+' '+mn+' '+r[3]+' '+r[0]+' '+uf+' '+UFN[uf])};ES.push(e);ESmap[e.code]=e})}
async function loadSet(uf){if(SSC[uf])return SSC[uf];showL('Carregando mapa de '+UFN[uf]+'…');
  const d=await fetch('data/'+uf+'_setores.json').then(r=>{if(!r.ok)throw new Error('falha');return r.json()});
  SSC[uf]=d.s.map(r=>{const s={m:r[0],b:r[1],p:r[2],d:r[3],a:[r[4],r[5],r[6],r[7]],r:r[8],ha:r[9],x:r[10],y:r[11],enc:r[12]};s.seg=[s.a[0]+.2*s.a[1],.8*s.a[1]+.2*s.a[2],.8*s.a[2],.6*s.a[3]];return s});showL('');return SSC[uf]}
let SS=[];
''')
rep("const active=ES.filter(e=>e.lat!=null);","let active=[];")
rep("function chooseSchool(code){const e=ESmap[code];if(!e)return;closeS();q.value=e.nome;st.center={lat:e.lat,lon:e.lon,name:e.nome,school:e};st.sel=null;",
    "function chooseSchool(code){const e=ESmap[code];if(!e)return;closeS();q.value=e.nome;st.center={lat:e.lat,lon:e.lon,name:e.nome,school:e,uf:e.uf};st.sel=null;")
rep("if(v.length<2||Math.abs(v[0])>90||v[0]>-2||v[0]<-8.5||v[1]>-37||v[1]<-42){err.textContent='Cole latitude e longitude de um ponto do Ceará, por exemplo -3.8163, -38.5390.';err.hidden=false;return}",
    "const uf=v.length>=2?(STATES.find(s=>v[1]>=s.bbox[0]-.05&&v[1]<=s.bbox[1]+.05&&v[0]>=s.bbox[2]-.05&&v[0]<=s.bbox[3]+.05)||{}).uf:null;\n  if(!uf){err.textContent='Cole latitude e longitude de um ponto dentro de um dos estados disponíveis, por exemplo -3.8163, -38.5390.';err.hidden=false;return}")
rep("st.center={lat:v[0],lon:v[1],name:nm,school:null};st.sel=null;run()});","st.center={lat:v[0],lon:v[1],name:nm,school:null,uf};st.sel=null;run()});")
rep("function run(){compute();","async function run(){try{SS=await loadSet(st.center.uf)}catch(_){showL('');alert0();return}compute();")
rep("function compute(){","function alert0(){const f=document.getElementById('rflag');f.hidden=false;f.innerHTML='<b>Não foi possível carregar o mapa deste estado.</b> Verifique a conexão e busque a escola de novo.'}\nfunction compute(){")
rep("const f=[];if(e){f.push(`<span>${e.mn}${e.bairro?', '+e.bairro:''}</span>`","const f=[];if(e){f.push(`<span>${e.mn}${e.bairro?', '+e.bairro:''}, ${e.uf}</span>`")
rep("m=c.mn||'Ceará'","m=c.mn||UFN[st.center.uf]")
rep("+' CE')","+' '+st.center.uf)")
rep("const all=ES.filter(e=>e.lat!=null&&e.tot>0&&(","const all=ES.filter(e=>e.uf===st.center.uf&&e.lat!=null&&e.tot>0&&(")
rep("COMP=ES.filter(e=>e.lat!=null&&(e.tot>0)","COMP=ES.filter(e=>e.uf===st.center.uf&&e.lat!=null&&(e.tot>0)")
rep("bind('radSeg',v=>{st.R=+v;st.sel=null;compute();","bind('radSeg',v=>{st.R=+v;st.sel=null;if(!SS.length)return;compute();")
old_start=t[t.index('function start(){'):t.index("window.addEventListener('hashchange'")]
rep(old_start,'''async function start(){showL('Carregando escolas…');
  const res=await Promise.all(STATES.map(s=>fetch('data/'+s.uf+'_esc.json').then(r=>r.json()).then(d=>[s.uf,d]).catch(()=>null)));
  res.forEach(x=>{if(x)addEsc(x[0],x[1])});active=ES.filter(e=>e.lat!=null);showL('');
  const ALL=['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO'];
  const on=STATES.map(s=>s.uf);
  document.getElementById('ufs').innerHTML='<span>Estados disponíveis:</span>'+STATES.map(s=>`<b title="${s.n} escolas privadas com alunos em 2025">${s.nome}</b>`).join('')+`<span class="soon">Em breve: ${ALL.filter(u=>!on.includes(u)).join(', ')}</span>`;
  const h=(location.hash||'').replace('#','');
  if(h.startsWith('e')&&ESmap[h.slice(1)]&&ESmap[h.slice(1)].lat!=null){const e=ESmap[h.slice(1)];q.value=e.nome;st.center={lat:e.lat,lon:e.lon,name:e.nome,school:e,uf:e.uf}}
  else st.center={lat:-3.8163473,lon:-38.5389519,name:'Colégio Futuro (exemplo)',school:null,uf:'CE'};
  try{SS=await loadSet(st.center.uf)}catch(_){showL('');alert0();return}
  compute();renderHead();renderStatements();renderHist();renderSegs();buildMap();renderMap();renderTable();renderDig()}
''')
rep("window.addEventListener('hashchange',()=>{const h=location.hash.slice(1);if(h.startsWith('e')&&ESmap[h.slice(1)]&&(!st.center.school||st.center.school.code!==h.slice(1)))chooseSchool(h.slice(1))});",
    "window.addEventListener('hashchange',()=>{const h=location.hash.slice(1);if(h.startsWith('e')&&ESmap[h.slice(1)]&&(!st.center||!st.center.school||st.center.school.code!==h.slice(1)))chooseSchool(h.slice(1))});")
rep("const re=()=>{renderHist();renderMap();renderTable()};","const re=()=>{if(!SS.length)return;renderHist();renderMap();renderTable()};")
rep('<footer><span>Reezu Marketing Educacional</span><span>Base: Censo Escolar 2025 e Censo IBGE 2022</span></footer>','<footer><span>Reezu Marketing Educacional</span><span>Base: Censo Escolar 2025 e Censo IBGE 2022</span></footer>')
# concorrentes: so escolas com segmento regular (exclui unidades so tecnicas ou EJA)
rep("e.lat!=null&&(e.tot>0)&&(!st.center.school","e.lat!=null&&(e.tot>0)&&e.seg.some(x=>x>0)&&(!st.center.school")
rep("e.lat!=null&&e.tot>0&&(!st.center.school","e.lat!=null&&e.tot>0&&e.seg.some(x=>x>0)&&(!st.center.school")
rep("Idades dos segmentos estimadas pelos grupos de 5 anos do IBGE.</p>","Idades dos segmentos estimadas pelos grupos de 5 anos do IBGE.</p>\n        <p><b>Concorrentes.</b> Entram só escolas com Educação Infantil, Fundamental ou Médio em 2025. Unidades que oferecem apenas curso técnico ou EJA ficam de fora, porque não disputam as mesmas famílias.</p>")
open(P+'/index.html','w').write(t)
json.dump(states,open(P+'/states.json','w'),ensure_ascii=False)
for f in sorted(os.listdir(P+'/data')): print(f, round(os.path.getsize(P+'/data/'+f)/1e6,2),'MB')
print('index', round(len(t)/1e3),'KB')
