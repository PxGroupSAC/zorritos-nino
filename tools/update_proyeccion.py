#!/usr/bin/env python3
"""Proyección de la temporada 2026-27 para Zorritos: descarga la lluvia diaria ERA5 (Open-Meteo, punto -3.68,-80.68),
compara la temporada en curso con los dos Niños extraordinarios (1982-83 y 1997-98) y con la climatología 1991-2020,
y genera el gráfico SVG + franja mensual de riesgo + tabla de hitos entre <!-- PROYECCION:START --> y <!-- PROYECCION:END -->
en zorritos-nino-mapa-peligro.html. Solo biblioteca estándar."""
import os, sys, json, subprocess, urllib.request, datetime, statistics
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE=os.path.join(root,'zorritos-nino-mapa-peligro.html')
today=datetime.date.today()
URL=f'https://archive-api.open-meteo.com/v1/archive?latitude=-3.68&longitude=-80.68&start_date=1981-01-01&end_date={today.isoformat()}&daily=precipitation_sum&timezone=America%2FLima'
def fetch(url):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        return urllib.request.urlopen(req,timeout=90).read().decode('utf-8')
    except Exception:
        return subprocess.run(['curl','-s','-m','90','-A','Mozilla/5.0',url],capture_output=True,text=True,check=True).stdout
d=json.loads(fetch(URL))['daily']
days=d['time']; pr=d['precipitation_sum']
daily=[(datetime.date.fromisoformat(t),v) for t,v in zip(days,pr) if v is not None]
last=daily[-1][0]
mon={}
for t,v in daily: mon[(t.year,t.month)]=mon.get((t.year,t.month),0)+v
MESES=['Set','Oct','Nov','Dic','Ene','Feb','Mar','Abr','May','Jun']
MNUM=[9,10,11,12,1,2,3,4,5,6]
def season(y0): return [mon.get((y0+(0 if m>=9 else 1),m)) for m in MNUM]
clim=[statistics.mean(mon.get((y+(0 if m>=9 else 1),m),0) for y in range(1991,2020)) for m in MNUM]
A83=season(1982); A98=season(1997)
cur_y0=today.year if today.month>=9 else today.year-1
CUR=season(cur_y0)
# months of the current season fully or partially observed
obs=[]
for i,m in enumerate(MNUM):
    y=cur_y0+(0 if m>=9 else 1); dt=datetime.date(y,m,1)
    if dt<=last:
        full=(y,m)!=(last.year,last.month)
        obs.append((i,CUR[i] or 0,full))
def onset(y0,th=25):
    seg=[(t,v) for t,v in daily if datetime.date(y0,9,1)<=t<=datetime.date(y0+1,6,30)]
    f=next((t for t,v in seg if v>=th),None)
    vals=[v for _,v in seg]; best=(0,None)
    for i in range(max(0,len(vals)-29)):
        s=sum(vals[i:i+30])
        if s>best[0]: best=(s,seg[i][0])
    return f,best
ON83=onset(1982); ON98=onset(1997)
fmt0=lambda v:f'{v:,.0f}'.replace(',',' ')
# ---------- SVG
W,H=960,430; L,R,T,B=56,24,44,46; pw=W-L-R; ph=H-T-B
ymax=max(800,max(v for v in A83+A98 if v)+40)
def X(i): return L+(i+0.5)*pw/10
def Y(v): return T+ph-v*ph/ymax
g=[f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-labelledby="proy-title" style="max-width:100%;height:auto;font-family:var(--body);font-size:13px">',
   '<title id="proy-title">Lluvia mensual en Zorritos durante los Niños de 1982-83 y 1997-98, climatología y temporada 2026-27 observada, con ventanas proyectadas</title>']
# milestone bands: inicio (mitad nov - mitad dic), pico (feb - mar), cola (abr - may)
def band(i0,i1,col,lab,op):
    x0=X(i0); x1=X(i1); g.append(f'<rect x="{x0:.1f}" y="{T}" width="{x1-x0:.1f}" height="{ph}" fill="{col}" opacity="{op}"/>')
    g.append(f'<text x="{(x0+x1)/2:.1f}" y="{T-8}" text-anchor="middle" fill="var(--fg)" style="font-size:12px;font-weight:600">{lab}</text>')
band(2.0,3.4,'var(--haz-h)','inicio probable',0.16)
band(4.6,6.4,'var(--haz-vh)','pico probable',0.14)
band(6.6,8.4,'var(--haz-m)','cola larga (1983)',0.18)
for v in range(0,int(ymax)+1,200):
    g.append(f'<line x1="{L}" x2="{L+pw}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="var(--line)" stroke-width="1"/>')
    g.append(f'<text x="{L-8}" y="{Y(v)+4:.1f}" text-anchor="end" fill="var(--muted)" style="font-family:var(--mono);font-size:12px">{v}</text>')
g.append(f'<text x="{L-44}" y="{T-26}" fill="var(--muted)" style="font-size:12px">mm/mes</text>')
for i,m in enumerate(MESES):
    yy=str(cur_y0 if MNUM[i]>=9 else cur_y0+1)[2:]
    g.append(f'<text x="{X(i):.1f}" y="{T+ph+18}" text-anchor="middle" fill="var(--muted)" style="font-family:var(--mono);font-size:11.5px">{m} {yy}</text>')
# band between analogs
top=[(X(i),Y(max(a,b))) for i,(a,b) in enumerate(zip(A83,A98))]; bot=[(X(i),Y(min(a,b))) for i,(a,b) in enumerate(zip(A83,A98))]
poly=' '.join(f'{x:.1f},{y:.1f}' for x,y in top+bot[::-1])
g.append(f'<polygon points="{poly}" fill="#c1272d" opacity=".10"/>')
def line(vals,col,lab,width=2,dash=''):
    pts=[(X(i),Y(v)) for i,v in enumerate(vals) if v is not None]
    g.append(f'<path d="M'+' L'.join(f'{x:.1f},{y:.1f}' for x,y in pts)+f'" fill="none" stroke="{col}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"{" stroke-dasharray=%s"%chr(34)+dash+chr(34) if dash else ""}/>')
    for i,v in enumerate(vals):
        if v is None: continue
        g.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3" fill="{col}" stroke="var(--panel)" stroke-width="1.5"><title>{lab}: {MESES[i]}, {fmt0(v)} mm</title></circle>')
    x,y=pts[-1]; ends.append((y,x,lab,col))
ends=[]
line(clim,'var(--muted)','Normal 1991‑2020',1.6,'5 4')
line(A83,'#1f4e79','1982‑83')
line(A98,'#2a9d8f','1997‑98')
ends.sort(); prev=-99
for y,x,lab,col in ends:
    y=max(y,prev+14); prev=y
    g.append(f'<text x="{x+6:.1f}" y="{y+4:.1f}" fill="var(--fg)" style="font-size:12px;font-weight:600"><tspan fill="{col}">■</tspan> {lab}</text>')
# observed bars
for i,v,full in obs:
    x=X(i); h=max(2,v*ph/ymax)
    g.append(f'<rect x="{x-14:.1f}" y="{Y(v):.1f}" width="28" height="{h:.1f}" fill="#c1272d" opacity="{1 if full else .55}" rx="3"><title>{cur_y0}‑{str(cur_y0+1)[2:]} observado: {MESES[i]}, {fmt0(v)} mm{"" if full else " (parcial)"}</title></rect>')
    g.append(f'<text x="{x:.1f}" y="{Y(v)-6:.1f}" text-anchor="middle" fill="var(--fg)" style="font-family:var(--mono);font-size:11.5px;font-weight:600">{fmt0(v)}{"" if full else "*"}</text>')
# today marker
ti=MNUM.index(last.month)+ (last.day-0.5)/30 - 0.5
xt=L+(ti+0.5)*pw/10
g.append(f'<line x1="{xt:.1f}" x2="{xt:.1f}" y1="{T}" y2="{T+ph}" stroke="var(--fg)" stroke-width="1.5" stroke-dasharray="3 3"/>')
g.append(f'<text x="{xt+5:.1f}" y="{T+14}" fill="var(--fg)" style="font-size:11.5px">datos al {last.day} {MESES[MNUM.index(last.month)].lower()}</text>')
g.append('</svg>')
svg='\n'.join(g)
legend=('<div class="legend"><span><i class="sw" style="background:#c1272d"></i>'+f'{cur_y0}‑{str(cur_y0+1)[2:]} observado (* mes incompleto)</span>'
        '<span><i class="sw line" style="background:#1f4e79"></i>1982‑83</span><span><i class="sw line" style="background:#2a9d8f"></i>1997‑98</span>'
        '<span><i class="sw" style="background:#c1272d;opacity:.15"></i>Rango entre los dos Niños extraordinarios</span><span><i class="sw line" style="background:var(--muted)"></i>Normal 1991‑2020</span></div>')
# ---------- risk strip
strip=[('Set','l1','Lluvias aisladas récord; mar ya extraordinario'),('Oct','l1','Preparación: limpiar cauces y pontones; oleajes'),('Nov','l2','Inicio probable de lluvias fuertes y primeras quebradas activas'),('Dic','l3','Lluvias intensas; quebradas y puente Bocapán en riesgo'),('Ene','l3','Magnitud extraordinaria (ENFEN); crecidas frecuentes'),('Feb','l4','Pico probable: 600–700 mm/mes en los análogos'),('Mar','l4','Pico probable; máximos de 30 días en 1983 y 1998'),('Abr','l3','Sigue muy lluvioso; suelos saturados'),('May','l2','Cola: 1983 siguió con 500 mm; 1998 bajó'),('Jun','l1','Declive; vigilar mar y rehabilitación')]
cells=''.join(f'<div class="cell {c}"><b>{m}</b>{t}</div>' for m,c,t in strip)
striphtml='<div class="strip">'+cells+'</div><div class="legend"><span><i class="sw" style="background:var(--haz-m)"></i>Vigilancia</span><span><i class="sw" style="background:var(--haz-h)"></i>Alto</span><span><i class="sw" style="background:var(--haz-vh)"></i>Muy alto</span><span><i class="sw" style="background:#7a1016"></i>Pico</span></div>'
# ---------- hitos table
def f(d): return d.strftime('%d/%m/%Y') if d else '—'
tbl=('<div class="tablewrap" style="margin-top:12px"><table style="min-width:640px"><thead><tr><th>Temporada</th><th>Primer día ≥ 25 mm</th><th>Mes más lluvioso</th><th>Peor ventana de 30 días</th><th class="num">Total set–jun (mm)</th></tr></thead><tbody>'
     f'<tr class="vh"><td>1982‑83</td><td>{f(ON83[0])}</td><td>{MESES[max(range(10),key=lambda i:A83[i] or 0)]}</td><td>{fmt0(ON83[1][0])} mm desde el {f(ON83[1][1])}</td><td class="num">{fmt0(sum(v or 0 for v in A83))}</td></tr>'
     f'<tr class="vh"><td>1997‑98</td><td>{f(ON98[0])}</td><td>{MESES[max(range(10),key=lambda i:A98[i] or 0)]}</td><td>{fmt0(ON98[1][0])} mm desde el {f(ON98[1][1])}</td><td class="num">{fmt0(sum(v or 0 for v in A98))}</td></tr>'
     f'<tr><td>Normal 1991‑2020</td><td>—</td><td>{MESES[max(range(10),key=lambda i:clim[i])]}</td><td>—</td><td class="num">{fmt0(sum(clim))}</td></tr>'
     f'<tr class="h"><td>{cur_y0}‑{str(cur_y0+1)[2:]} (en curso, al {f(last)})</td><td>{f(next((t for t,v in daily if t>=datetime.date(cur_y0,9,1) and v>=25),None))}</td><td>—</td><td>—</td><td class="num">{fmt0(sum(v for _,v,_ in obs))}</td></tr>'
     '</tbody></table></div>')
note=f'<p class="note" style="margin-top:8px">Lluvia del reanálisis ERA5 (ECMWF, 0,25°) en el punto de Zorritos vía Open‑Meteo; reproduce bien el calendario de cada temporada pero subestima los extremos diarios frente a las estaciones de SENAMHI. Datos hasta el {f(last)}.</p>'
# ---------- datos diarios de la temporada en JSON (los lee la sección #seguimiento)
dd={t:v for t,v in daily}
def dayseries(y0,end=None):
    out=[]; t=datetime.date(y0,9,1); end=end or datetime.date(y0+1,6,30)
    while t<=end:
        v=dd.get(t); out.append(None if v is None else round(v,1)); t+=datetime.timedelta(days=1)
    return out
segjson=('<script type="application/json" id="seg-lluvia">'+json.dumps({'inicio':f'{cur_y0}-09-01','hasta':last.isoformat(),'mm':dayseries(cur_y0,last),'a83':dayseries(1982),'a98':dayseries(1997)},separators=(',',':'))+'</script>')
body=svg+'\n'+legend+'\n<h3 style="margin-top:18px">Mes a mes: qué esperar en Zorritos</h3>\n'+striphtml+'\n'+tbl+'\n'+note+'\n'+segjson
s=open(PAGE,encoding='utf-8').read()
a=s.index('<!-- PROYECCION:START -->'); b=s.index('<!-- PROYECCION:END -->')+len('<!-- PROYECCION:END -->')
# Sello de regeneración: conserva la fecha anterior si los datos no cambiaron.
import re
old=s[a:b]; m=re.search(r'<p class="stamp"[^\n]*\n',old)
old_body=old[len('<!-- PROYECCION:START -->\n'):-len('\n<!-- PROYECCION:END -->')]
if m: old_body=old_body.replace(m.group(0),'',1)
if m and old_body==body:
    stamp=m.group(0).rstrip('\n')
else:
    hoy=datetime.date.today(); M12=['ene','feb','mar','abr','may','jun','jul','ago','set','oct','nov','dic']
    stamp=f'<p class="stamp" data-upd="{hoy.isoformat()}" data-rev="1">Gráfico regenerado el {hoy.day} {M12[hoy.month-1]} {hoy.year} con lluvia ERA5 hasta el {last.day} {M12[last.month-1]}.</p>'
block='<!-- PROYECCION:START -->\n'+stamp+'\n'+body+'\n<!-- PROYECCION:END -->'
open(PAGE,'w',encoding='utf-8').write(s[:a]+block+s[b:])
print('proyección actualizada; ERA5 hasta',last,'| temporada en curso',[(MESES[i],round(v)) for i,v,_ in obs],'| análogos', ON83, ON98)
subprocess.run([sys.executable,os.path.join(root,'tools','build_index.py')],check=True)
