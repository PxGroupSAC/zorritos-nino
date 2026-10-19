#!/usr/bin/env python3
"""Descarga los índices Niño 1+2 de NOAA CPC (OISST v2.1 mensual y semanal), construye el gráfico SVG de anomalía
de temperatura del mar y lo inserta entre <!-- SST-CHART:START --> y <!-- SST-CHART:END --> en
zorritos-nino-mapa-peligro.html. Luego regenera index.html. Solo usa la biblioteca estándar."""
import os, re, sys, subprocess, urllib.request, ssl, datetime
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE=os.path.join(root,'zorritos-nino-mapa-peligro.html')
MONTHLY='https://www.cpc.ncep.noaa.gov/data/indices/sstoi.indices'
WEEKLY='https://www.cpc.ncep.noaa.gov/data/indices/wksst9120.for'
def fetch(url):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        return urllib.request.urlopen(req,timeout=60).read().decode('latin-1')
    except Exception:
        return subprocess.run(['curl','-s','-m','60','-A','Mozilla/5.0',url],capture_output=True,text=True,check=True).stdout
mon={}
for line in fetch(MONTHLY).splitlines():
    p=line.split()
    if len(p)>=4 and p[0].isdigit() and p[1].isdigit():
        mon[(int(p[0]),int(p[1]))]=float(p[3])
weeks=[]
for line in fetch(WEEKLY).splitlines():
    m=re.match(r'^\s*(\d{2})([A-Z]{3})(\d{4})\s+(\d+\.\d)\s*(-?\d+\.\d)',line)
    if m:
        d=datetime.date(int(m.group(3)),['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'].index(m.group(2))+1,int(m.group(1)))
        weeks.append((d,float(m.group(5))))
assert mon and weeks, 'sin datos'
lastw=weeks[-1]; lastm=max(mon)
EV=[(1982,'1982‑83','#1f4e79'),(1997,'1997‑98','#2a9d8f'),(2015,'2015‑16','#8e5bd1'),(2023,'2023‑24','#b58900'),(2026,'2026‑27','#c1272d')]
MES=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Set','Oct','Nov','Dic']
def series(y0):
    out=[]
    for k in range(18):
        y=y0+k//12; m=k%12+1
        out.append(mon.get((y,m)))
    return out
data={y0:series(y0) for y0,_,_ in EV}
peaks={}
for y0,lab,_ in EV:
    vals=[(v,k) for k,v in enumerate(data[y0]) if v is not None]
    if vals:
        v,k=max(vals); peaks[y0]=(v,MES[k%12]+' '+str(y0+k//12))
# geometry
W,H=960,440; L,R,T,B=58,150,18,56
pw=W-L-R; ph=H-T-B; ymin,ymax=-2.0,6.0
def X(k): return L+k*pw/17
def Y(v): return T+(ymax-v)*ph/(ymax-ymin)
def fmt(v): return ('+' if v>=0 else '−')+f'{abs(v):.1f}'.replace('.',',')
g=[]
g.append(f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-labelledby="tsm-title" style="max-width:100%;height:auto;font-family:var(--body);font-size:13px">')
g.append('<title id="tsm-title">Anomalía mensual de la temperatura superficial del mar en la región Niño 1+2 para cinco episodios El Niño</title>')
for v in range(int(ymin),int(ymax)+1):
    g.append(f'<line x1="{L}" x2="{L+pw}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="var(--line)" stroke-width="{2 if v==0 else 1}"/>')
    g.append(f'<text x="{L-8}" y="{Y(v)+4:.1f}" text-anchor="end" fill="var(--muted)" style="font-family:var(--mono);font-size:12px">{fmt(v) if v!=0 else "0"}</text>')
for v,lab in [(0.4,'débil'),(1.0,'moderado'),(1.7,'fuerte'),(3.0,'extraordinario')]:
    g.append(f'<line x1="{L}" x2="{L+pw}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="var(--haz-h)" stroke-width="1" stroke-dasharray="4 4" opacity=".7"/>')
    g.append(f'<text x="{L+4}" y="{Y(v)-4:.1f}" fill="var(--haz-h)" style="font-size:11px;letter-spacing:.04em">{lab} ≥ {fmt(v)} °C</text>')
for k in range(18):
    yy=k//12; lab=MES[k%12]+("'" if yy==1 else '')
    g.append(f'<text x="{X(k):.1f}" y="{T+ph+18}" text-anchor="middle" fill="var(--muted)" style="font-family:var(--mono);font-size:11px">{lab}</text>')
g.append(f'<text x="{L}" y="{T+ph+40}" fill="var(--muted)" style="font-size:12px">Meses del año del evento; las marcas con apóstrofo son del año siguiente. Anomalía respecto a 1991‑2020.</text>')
g.append(f'<text x="{L-44}" y="{T-4}" fill="var(--muted)" style="font-size:12px">°C</text>')
ends=[]
for y0,lab,col in EV:
    pts=[(X(k),Y(v),k,v) for k,v in enumerate(data[y0]) if v is not None]
    if not pts: continue
    cur=(y0==2026)
    d='M'+' L'.join(f'{x:.1f},{y:.1f}' for x,y,_,_ in pts)
    g.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{3.2 if cur else 2}" stroke-linejoin="round" stroke-linecap="round"/>')
    for x,y,k,v in pts:
        g.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{4 if cur else 3}" fill="{col}" stroke="var(--panel)" stroke-width="1.5"><title>{lab}: {MES[k%12]} {y0+k//12}, {fmt(v)} °C</title></circle>')
    ends.append((pts[-1][1],pts[-1][0],lab,col,cur))
# weekly latest point
kw=(lastw[0].year-2026)*12+lastw[0].month-1
if 0<=kw<18:
    xw,yw=X(kw),Y(lastw[1])
    g.append(f'<path d="M{xw:.1f},{yw-7:.1f} L{xw+7:.1f},{yw:.1f} L{xw:.1f},{yw+7:.1f} L{xw-7:.1f},{yw:.1f} Z" fill="var(--panel)" stroke="#c1272d" stroke-width="2.5"><title>Semana del {lastw[0].strftime("%d/%m/%Y")}: {fmt(lastw[1])} °C</title></path>')
    g.append(f'<text x="{xw+10:.1f}" y="{yw-10:.1f}" fill="var(--fg)" style="font-size:12px;font-weight:600">{fmt(lastw[1])} °C · semana del {lastw[0].day} {MES[lastw[0].month-1].lower()}</text>')
# direct labels at line ends, de-overlapped
ends.sort()
prev=-99
for y,x,lab,col,cur in ends:
    y=max(y,prev+14); prev=y
    g.append(f'<text x="{x+8:.1f}" y="{y+4:.1f}" fill="var(--fg)" style="font-size:12.5px;font-weight:{700 if cur else 500}"><tspan fill="{col}">■</tspan> {lab}</text>')
g.append('</svg>')
svg='\n'.join(g)
legend='<div class="legend">'+''.join(f'<span><i class="sw" style="background:{col}"></i>{lab}</span>' for _,lab,col in EV)+'<span><i class="sw ring" style="border-color:#c1272d;border-radius:0;transform:rotate(45deg);width:11px;height:11px"></i>Último dato semanal</span><span><i class="sw line" style="background:var(--haz-h)"></i>Umbrales ICEN (ENFEN)</span></div>'
rows=''.join('<tr><td>'+MES[k%12]+("'" if k>=12 else '')+'</td>'+''.join('<td class="num">'+(fmt(data[y0][k])+' °C' if data[y0][k] is not None else '—')+'</td>' for y0,_,_ in EV)+'</tr>' for k in range(18))
table='<details style="margin-top:8px"><summary style="cursor:pointer;color:var(--accent)">Ver la tabla de datos</summary><div class="tablewrap" style="margin-top:8px"><table style="min-width:520px"><thead><tr><th>Mes</th>'+''.join(f'<th>{lab}</th>' for _,lab,_ in EV)+'</tr></thead><tbody>'+rows+'</tbody></table></div></details>'
lm=f'{MES[lastm[1]-1].lower()} {lastm[0]}'
note=(f'<p class="note" style="margin-top:8px">Último dato mensual: {lm}, <b>{fmt(mon[lastm])} °C</b>. Última semana ({lastw[0].strftime("%d/%m/%Y")}): <b>{fmt(lastw[1])} °C</b>. '
      f'Máximos mensuales: 1982‑83 {fmt(peaks[1982][0])} °C ({peaks[1982][1]}), 1997‑98 {fmt(peaks[1997][0])} °C ({peaks[1997][1]}), 2023‑24 {fmt(peaks[2023][0])} °C ({peaks[2023][1]}). '
      f'Fuente: NOAA CPC, OISST v2.1, región Niño 1+2 (0–10° S, 90–80° O). Actualizado el {datetime.date.today().strftime("%d/%m/%Y")}.</p>')
block='<!-- SST-CHART:START -->\n'+svg+'\n'+legend+'\n'+note+'\n'+table+'\n<!-- SST-CHART:END -->'
s=open(PAGE,encoding='utf-8').read()
a=s.index('<!-- SST-CHART:START -->'); b=s.index('<!-- SST-CHART:END -->')+len('<!-- SST-CHART:END -->')
s=s[:a]+block+s[b:]
open(PAGE,'w',encoding='utf-8').write(s)
print('gráfico TSM actualizado:', lm, fmt(mon[lastm]), '| semana', lastw[0], fmt(lastw[1]), '| picos', {k:(round(v[0],2),v[1]) for k,v in peaks.items()})
subprocess.run([sys.executable,os.path.join(root,'tools','update_proyeccion.py')],check=True)
