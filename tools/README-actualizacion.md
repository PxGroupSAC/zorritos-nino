# Cómo actualizar "Zorritos ante El Niño"

Sitio público: https://pxgroupsac.github.io/zorritos-nino/ (GitHub Pages publica `index.html` desde `main`, tarda 1–2 min).

## Archivos
- `zorritos-nino-mapa-peligro.html`: la página. **Es el único archivo que se edita a mano.** Lleva las imágenes incrustadas (data URIs), por eso pesa 4,5 MB; no tocar las cadenas `data:image/...`.
- `index.html`: se genera con `python3 tools/build_index.py` (envuelve la página en `<!doctype html><head><body>`). Nunca editarlo a mano.
- `tools/update_sst.py`: descarga los índices Niño 1+2 de NOAA CPC (mensual `sstoi.indices` y semanal `wksst9120.for`), regenera el gráfico SVG de anomalía de temperatura del mar entre `<!-- SST-CHART:START -->` y `<!-- SST-CHART:END -->` y luego llama a `build_index.py`.
- `zorritos-mapa-general.jpg`: mapa estático de referencia (no cambia).

## Marcadores en la página
| Marcador | Qué va ahí |
|---|---|
| `<!-- NOVEDADES:START -->` … `<!-- NOVEDADES:END -->` | Contenido completo de la sección "Novedades al <fecha>": `div.sec-head` + `div.news` con tarjetas `div.callout` (`div.d` fecha y fuente, `h3`, `ul`). `callout vh` para lo más grave. |
| `<!-- CRONOLOGIA:END -->` | Insertar antes de este marcador los `div.ev` nuevos (clases: `q` lluvias/quebradas, `m` mar, `vh` muy grave, `a` infraestructura/institucional). Formato: `<div class="ev q"><div class="when"><b>2026</b>d mes</div><div><h3>Título</h3><p>Texto.</p><p class="src">Fuente (fecha).</p></div></div>` |
| `<!-- FUENTES:END -->` | Insertar antes un `<li>` con las fuentes nuevas enlazadas. |
| `<!-- SST-CHART:START/END -->` | Lo regenera `update_sst.py`; no editar a mano. |

Además, en cada actualización cambiar:
- `div.eyebrow`: "... · actualizada el <d de mes de aaaa>".
- `span.upd` dentro del `h1`: "Actualizado <d mes aaaa>".
- Primer `div.callout.vh` del encabezado ("Alerta vigente") si el ENFEN emitió comunicado nuevo o cambió el estado de emergencia.

## Procedimiento semanal
1. Buscar novedades de los últimos 7 días: ENFEN (comunicados), SENAMHI (avisos para Tumbes), INDECI/COEN (reportes de emergencia de Tumbes), DHN (oleaje), Gobierno/PCM/MEF (decretos, prórrogas, transferencias), ANA/MVCS/Midagri (obras en Tumbes), prensa sobre Zorritos, Bocapán, Acapulco, Caleta Grau, Cancas, Casitas y Contralmirante Villar.
2. Editar la página en los marcadores indicados. Español neutro, frases cortas, cada dato con fuente y fecha, sin inventar cifras.
3. `python3 tools/update_sst.py` (si falla la red, al menos `python3 tools/build_index.py`).
4. Comprobar: `grep -c 'NOVEDADES:START\|NOVEDADES:END\|CRONOLOGIA:END\|FUENTES:END\|SST-CHART:START' zorritos-nino-mapa-peligro.html` debe dar 5, y `grep -c 'actualizada el' index.html` debe dar 1 con la fecha nueva.
5. `git add -A && git commit -m "Actualización al <fecha>" && git push origin main`.

El artefacto de claude.ai (https://claude.ai/artifact/5JqQ16Bq1VTveYAG7ncQMC) se republica desde Claude Code con el mismo archivo `zorritos-nino-mapa-peligro.html`; la rutina en la nube no lo hace.
