#!/bin/bash
# Actualiza el semáforo SILVIA (SENAMHI) desde esta Mac y lo publica en GitHub Pages.
# SENAMHI no responde a los servidores de GitHub ni a proxies en la nube, por eso este paso corre aquí,
# programado con launchd (~/Library/LaunchAgents/com.pxgroup.zorritos-silvia.plist, 14:40 y 20:10 hora local).
# Registro: .silvia-local.log en la carpeta del repositorio.
set -u
REPO="/Users/fla/GIT/Niño"
LOG="$REPO/.silvia-local.log"
export PATH="/opt/homebrew/bin:/usr/local/bin:/Library/Frameworks/Python.framework/Versions/3.13/bin:/usr/bin:/bin"
export LANG="es_PE.UTF-8"
cd "$REPO" || exit 1
{
  echo "=== $(date '+%Y-%m-%d %H:%M:%S %Z')"
  if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "hay cambios locales sin confirmar en el repositorio; no toco nada"; exit 0
  fi
  git pull -q --rebase origin main || { echo "git pull --rebase falló"; exit 1; }
  python3 tools/update_silvia.py || { echo "update_silvia.py falló"; exit 1; }
  if git diff --quiet; then echo "sin cambios"; exit 0; fi
  git add zorritos-nino-mapa-peligro.html index.html
  git commit -q -m "Semáforo SILVIA actualizado ($(date '+%Y-%m-%d'))" || { echo "commit falló"; exit 1; }
  git push -q origin main && echo "publicado en GitHub"
} >> "$LOG" 2>&1
