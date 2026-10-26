# Cómo actualizar "Zorritos ante El Niño"

Sitio público: https://pxgroupsac.github.io/zorritos-nino/ (GitHub Pages publica `index.html` desde `main`, tarda 1–2 min).

## Archivos
- `zorritos-nino-mapa-peligro.html`: la página. **Es el único archivo que se edita a mano.** Lleva las imágenes incrustadas (data URIs), por eso pesa 4,5 MB; no tocar las cadenas `data:image/...`.
- `index.html`: se genera con `python3 tools/build_index.py` (envuelve la página en `<!doctype html><head><body>`). Nunca editarlo a mano.
- `tools/update_sst.py`: descarga los índices Niño 1+2 de NOAA CPC (mensual `sstoi.indices` y semanal `wksst9120.for`), regenera el gráfico SVG de anomalía de temperatura del mar entre `<!-- SST-CHART:START -->` y `<!-- SST-CHART:END -->` y luego llama a `update_proyeccion.py`.
- `tools/update_proyeccion.py`: descarga la lluvia diaria ERA5 del punto de Zorritos (Open-Meteo), regenera el gráfico de proyección, la franja mensual de riesgo y la tabla de hitos entre `<!-- PROYECCION:START -->` y `<!-- PROYECCION:END -->`, y llama a `build_index.py`. Los textos de los tres hitos (sección `#proyeccion`) son editables a mano si ENFEN o SENAMHI cambian el calendario.
- `.github/workflows/update-charts.yml`: GitHub Actions ejecuta `update_sst.py` los martes y viernes y hace commit solo si cambió algo. Ambos scripts escriben al inicio de su bloque un sello `<p class="stamp" data-upd="AAAA-MM-DD" data-rev="1">Gráfico regenerado el …</p>` que conserva la fecha anterior cuando los datos no cambiaron.
- `zorritos-mapa-general.jpg`: mapa estático de referencia (no cambia).

## Marcadores en la página
| Marcador | Qué va ahí |
|---|---|
| `<!-- NOVEDADES:START -->` … `<!-- NOVEDADES:END -->` | Contenido completo de la sección "Novedades al <fecha>": `div.sec-head` + `div.news` con tarjetas `div.callout` (`div.d` fecha y fuente, `h3`, `ul`). `callout vh` para lo más grave. |
| `<!-- CRONOLOGIA:END -->` | Insertar antes de este marcador los `div.ev` nuevos (clases: `q` lluvias/quebradas, `m` mar, `vh` muy grave, `a` infraestructura/institucional). Formato: `<div class="ev q" data-upd="AAAA-MM-DD"><div class="when"><b>2026</b>d mes</div><div><h3>Título</h3><p>Texto.</p><p class="src">Fuente (fecha).</p></div></div>` |
| `<!-- FUENTES:END -->` | Insertar antes un `<li data-upd="AAAA-MM-DD">Actualización del d de mes de aaaa: …</li>` con las fuentes nuevas enlazadas. |
| `<!-- HISTORIAL:START -->` … `<!-- HISTORIAL:END -->` | Historial de ediciones, la más reciente primero. En cada actualización insertar **justo después de `<!-- HISTORIAL:START -->`** un `div.h-ent`: `<div class="h-ent" data-date="AAAA-MM-DD"><div class="when"><b>d mes</b>aaaa · día de la semana</div><ul><li>…</li></ul></div>` con 2–4 viñetas de lo que cambió (novedades añadidas, entradas de cronología, cambios en Alerta vigente, gráficos). No borrar entradas antiguas. |
| `<!-- SST-CHART:START/END -->` | Lo regenera `update_sst.py`; no editar a mano. |
| `<!-- PROYECCION:START/END -->` | Lo regenera `update_proyeccion.py`; no editar a mano. |

## Marcado de novedades (etiquetas "Nuevo" / "Actualizado")
Un script al final de la página lee los atributos `data-upd` y pone etiquetas solas; no hay que escribir las etiquetas a mano.
- **Elemento nuevo** (tarjeta `div.callout`, entrada `div.ev`, fuente `li`): añadir `data-upd="AAAA-MM-DD"` con la fecha de la edición.
- **Elemento existente revisado** (por ejemplo la tarjeta "Alerta vigente" del encabezado o una tarjeta de Novedades que se reescribe): poner `data-upd` con la fecha de hoy **y** `data-rev="1"`.
- **No quitar** el `data-upd` de los elementos antiguos: el script solo etiqueta la última edición (rojo "Nuevo", naranja "Actualizado") y la anterior (gris); lo demás no muestra nada.
- El `span.upd` del `h1` lleva `data-date="AAAA-MM-DD"` con la fecha de la edición; el script la usa junto con las fechas del historial para saber cuál es la edición actual.
- El resumen "Nuevo en esta edición" de la cabecera (`div#whatsnew`) se genera solo a partir de los elementos marcados.

Además, en cada actualización cambiar:
- `div.eyebrow`: "... · actualizada el <d de mes de aaaa>".
- `span.upd` dentro del `h1`: texto "Actualizado <d mes aaaa>" y atributo `data-date`.
- Primer `div.callout.vh` del encabezado ("Alerta vigente") si el ENFEN emitió comunicado nuevo o cambió el estado de emergencia (y entonces `data-upd` de hoy + `data-rev="1"`).

## Procedimiento semanal
1. Buscar novedades de los últimos 7 días: ENFEN (comunicados), SENAMHI (avisos para Tumbes), INDECI/COEN (reportes de emergencia de Tumbes), DHN (oleaje), Gobierno/PCM/MEF (decretos, prórrogas, transferencias), ANA/MVCS/Midagri (obras en Tumbes), prensa sobre Zorritos, Bocapán, Acapulco, Caleta Grau, Cancas, Casitas y Contralmirante Villar.
2. Editar la página en los marcadores indicados, con `data-upd` en todo lo nuevo o revisado y una entrada nueva en el historial. Español neutro, frases cortas, cada dato con fuente y fecha, sin inventar cifras.
3. `python3 tools/update_sst.py` (si falla la red, al menos `python3 tools/build_index.py`).
4. Comprobar: `grep -c 'NOVEDADES:START\|NOVEDADES:END\|CRONOLOGIA:END\|FUENTES:END\|SST-CHART:START\|SST-CHART:END\|PROYECCION:START\|PROYECCION:END\|HISTORIAL:START\|HISTORIAL:END' zorritos-nino-mapa-peligro.html` debe dar 10; `grep -c 'data-upd="<fecha de hoy>"' zorritos-nino-mapa-peligro.html` debe ser ≥ 1; `grep -c 'actualizada el' index.html` debe dar 1 con la fecha nueva.
5. `git add -A && git commit -m "Actualización al <fecha>" && git push origin main`.

El artefacto de claude.ai (https://claude.ai/artifact/5JqQ16Bq1VTveYAG7ncQMC) se republica desde Claude Code con el mismo archivo `zorritos-nino-mapa-peligro.html`; la rutina en la nube no lo hace.
