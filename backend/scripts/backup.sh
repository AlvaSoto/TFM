#!/usr/bin/env bash
# Backup nocturno con rotación de 14 días de los datos vivos del piloto:
#   - pilot_readings.db  (lecturas reales — lo irreemplazable)
#   - fleet_scores.json  (estado de alertas)
#   - tenants.json       (clientes y credenciales)
#
# Programar:  30 5 * * *  /ruta/al/backend/scripts/backup.sh /ruta/backups
# Restaurar:  sqlite3 comprueba integridad; copiar el fichero de vuelta basta.
set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:-$BACKEND_DIR/backups}"
STAMP="$(date +%Y%m%d_%H%M)"
KEEP_DAYS=14

mkdir -p "$DEST"

# SQLite: backup consistente aunque haya escrituras concurrentes
if [ -f "$BACKEND_DIR/data/pilot_readings.db" ]; then
  sqlite3 "$BACKEND_DIR/data/pilot_readings.db" ".backup '$DEST/pilot_readings_$STAMP.db'"
fi

for f in fleet_scores.json tenants.json; do
  [ -f "$BACKEND_DIR/data/$f" ] && cp "$BACKEND_DIR/data/$f" "$DEST/${f%.json}_$STAMP.json"
done

# Rotación
find "$DEST" -type f \( -name "*.db" -o -name "*.json" \) -mtime +$KEEP_DAYS -delete

echo "[BACKUP] $STAMP completado en $DEST ($(ls "$DEST" | wc -l | tr -d ' ') ficheros retenidos)"
