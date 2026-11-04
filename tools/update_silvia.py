#!/usr/bin/env python3
"""Semáforo SILVIA (SENAMHI) para Contralmirante Villar.

Descarga del servicio WFS de IDESEP las cuencas de SILVIA (Sistema de Monitoreo de Movimientos en Masa por Lluvias
Intensas) con su nivel diario (1 normal, 2 amarillo, 3 naranja, 4 rojo) para el día observado y tres días de pronóstico,
calcula el nivel máximo de las cuencas que tocan cada distrito (Zorritos, Casitas, Canoas de Punta Sal), lee el aviso
vigente de la página de SILVIA y escribe todo como JSON entre <!-- SILVIA:START --> y <!-- SILVIA:END --> en
zorritos-nino-mapa-peligro.html, conservando el historial diario ya guardado en la página. Solo biblioteca estándar."""
import os, re, sys, json, time, datetime, subprocess, urllib.request, html as htmlmod

root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE=os.path.join(root,'zorritos-nino-mapa-peligro.html')
GEO=os.path.join(root,'tools','data','distritos_contralmirante_villar.geojson')
BBOX='-81.06,-4.23,-80.50,-3.62'
WFS=('https://idesep.senamhi.gob.pe/geoserver/silvia/ows?service=WFS&version=1.0.0&request=GetFeature'
     '&typeName=silvia:{layer}&outputFormat=application/json&bbox='+BBOX+',EPSG:4326')
LAYERS=[('obs','cuencas_nivel_12_silvia'),('p1','cuencas_nivel_12_prono1_silvia'),
        ('p2','cuencas_nivel_12_prono2_silvia'),('p3','cuencas_nivel_12_prono3_silvia')]
DIST=[('zorritos','Zorritos'),('casitas','Casitas'),('canoas','Canoas de Punta Sal')]
MES=['ene','feb','mar','abr','may','jun','jul','ago','set','oct','nov','dic']
NIVEL={'uno':1,'dos':2,'tres':3,'cuatro':4}
NOMBRE={1:'normal',2:'amarillo',3:'naranja',4:'rojo'}

def fetch(url,timeout=240,tries=3):
    last=None
    for i in range(tries):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (zorritos-nino)'})
            return urllib.request.urlopen(req,timeout=timeout).read()
        except Exception as e:
            last=e
            try:
                r=subprocess.run(['curl','-sS','-m',str(timeout),'-A','Mozilla/5.0',url],capture_output=True,check=True)
                if r.stdout: return r.stdout
            except Exception as e2:
                last=e2
            time.sleep(15*(i+1))
    raise last

def pip(pt,ring):
    x,y=pt; inside=False; n=len(ring)
    for i in range(n):
        x1,y1=ring[i][0],ring[i][1]; x2,y2=ring[(i+1)%n][0],ring[(i+1)%n][1]
        if (y1>y)!=(y2>y):
            xi=x1+(y-y1)*(x2-x1)/(y2-y1)
            if xi>x: inside=not inside
    return inside

def fd(iso):
    d=datetime.date.fromisoformat(iso[:10]); return f'{d.day} {MES[d.month-1]}'

# ---------- distritos
distritos={f['properties']['name']:f['geometry']['coordinates'][0] for f in json.load(open(GEO,encoding='utf-8'))['features']}

# ---------- cuencas y niveles
def niveles(layer):
    d=json.loads(fetch(WFS.format(layer=layer)).decode('utf-8'))
    feats=d.get('features',[])
    if not feats: raise RuntimeError('sin cuencas en '+layer)
    fecha=max(f['properties'].get('fecha','') for f in feats)[:10]
    out={}; used={}
    for key,name in DIST:
        ring=distritos[name]; best=1; n=0
        for f in feats:
            pts=[p for poly in f['geometry']['coordinates'] for p in poly[0]]
            k=sum(1 for p in pts if pip(p,ring))
            if k>=3 or (pts and k/len(pts)>=0.1):
                n+=1; best=max(best,int(f['properties'].get('silvia') or 1))
        out[key]=best; used[key]=n
    out['provincia']=max(out[k] for k,_ in DIST)
    return fecha,out,used,len(feats)

res={}
for key,layer in LAYERS:
    res[key]=niveles(layer)
    print(key,res[key][0],res[key][1],'cuencas',res[key][3])

# ---------- aviso vigente
def aviso():
    try:
        s=fetch('https://www.senamhi.gob.pe/?p=silvia',timeout=60,tries=2).decode('latin-1')
    except Exception as e:
        print('aviso: no se pudo leer la página', e); return None
    m=re.search(r'N&deg;\s*(\d+)\s*-\s*(\d{4})',s); n=re.search(r'id="spanNivel"\s+class="(\w+)"[^>]*>\s*NIVEL\s+(\w+)',s)
    f=re.search(r'id="spanFecha"[^>]*>\s*([^<]*?)\s*</label>\s*-\s*(\d{1,2}:\d{2})',s)
    dur=re.search(r'Duraci&oacute;n:.*?<span[^>]*>\s*([^<]+?)\s*</span>',s,re.S)
    dep=re.search(r'id="ubicacionDep2".*?</p>',s,re.S)
    deps=[]
    if dep:
        t=htmlmod.unescape(re.sub(r'<[^>]+>','',dep.group(0)))
        deps=[x.strip() for x in t.split(',') if x.strip() and x.strip().upper()==x.strip()]
    if not (m and n): return None
    return {'numero':f'{m.group(1)}-{m.group(2)}','nivel':n.group(2).lower(),'nivel_num':NIVEL.get(n.group(1),None),
            'inicio':(htmlmod.unescape(f.group(1)).strip()+' '+f.group(2)) if f else '','duracion':dur.group(1).strip() if dur else '',
            'departamentos':deps}
av=aviso(); print('aviso',av)

# ---------- JSON (con historial previo)
s=open(PAGE,encoding='utf-8').read()
a=s.index('<!-- SILVIA:START -->'); b=s.index('<!-- SILVIA:END -->')+len('<!-- SILVIA:END -->')
old=s[a:b]
mj=re.search(r'<script type="application/json" id="silvia-data">(.*?)</script>',old,re.S)
try: prev=json.loads(mj.group(1)) if mj else {}
except Exception: prev={}
hist=[h for h in prev.get('historial',[]) if isinstance(h,dict) and h.get('fecha')]
fobs,lv,used,ncu=res['obs']
entry=dict(fecha=fobs,**lv)
if av: entry['aviso']=f"{av['numero']} {av['nivel']}"
hist=[h for h in hist if h['fecha']!=fobs]+[entry]
hist.sort(key=lambda h:h['fecha']); hist=hist[-400:]
data={'fuente':'SENAMHI, SILVIA (servicio WFS de IDESEP, cuencas de nivel 12)','actualizado':datetime.date.today().isoformat(),
      'obs':entry,'prono':[dict(fecha=res[k][0],**res[k][1]) for k in ('p1','p2','p3')],
      'cuencas':used,'aviso':av,'historial':hist}
body='<script type="application/json" id="silvia-data">'+json.dumps(data,ensure_ascii=False,separators=(',',':'))+'</script>'
# sello: conserva la fecha si el JSON no cambió
ms=re.search(r'<p class="stamp"[^\n]*\n',old)
old_body=old[len('<!-- SILVIA:START -->\n'):-len('\n<!-- SILVIA:END -->')]
if ms: old_body=old_body.replace(ms.group(0),'',1)
if ms and old_body==body:
    stamp=ms.group(0).rstrip('\n')
else:
    hoy=datetime.date.today()
    stamp=(f'<p class="stamp" data-upd="{hoy.isoformat()}" data-rev="1">Semáforo actualizado el {hoy.day} {MES[hoy.month-1]} {hoy.year} '
           f'con los datos de SENAMHI del {fd(fobs)} (observado) y pronóstico hasta el {fd(res["p3"][0])}'
           +(f'; aviso SILVIA vigente N° {av["numero"]}, nivel {av["nivel"]}' if av else '')+'.</p>')
block='<!-- SILVIA:START -->\n'+stamp+'\n'+body+'\n<!-- SILVIA:END -->'
open(PAGE,'w',encoding='utf-8').write(s[:a]+block+s[b:])
print('semáforo escrito:',fobs,lv,'| historial',len(hist),'días')
subprocess.run([sys.executable,os.path.join(root,'tools','build_index.py')],check=True)
