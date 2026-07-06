# 💧 Smart Water Monitor

**Detección temprana de fugas de agua para hoteles, municipios y gestoras.**

Monitorización continua de contadores con doble verificación — la física del
contador confirma, la IA amplía la búsqueda — y traducción de cada anomalía a
litros y euros. Multi-tenant, white-label y desplegable en la infraestructura
del cliente.

> 🌐 Landing de producto: [`landing/index.html`](landing/index.html) ·
> 📋 Propuesta de piloto: [`docs/PROPUESTA_PILOTO_PLANTILLA.md`](docs/PROPUESTA_PILOTO_PLANTILLA.md) ·
> 🗺 Guía go-to-market: [`docs/GUIA_GO_TO_MARKET.md`](docs/GUIA_GO_TO_MARKET.md)

---

## Cómo detecta

Ensemble de dos detectores independientes por segmento:

| Detector | Qué ve | Papel |
|---|---|---|
| **Caudal Mínimo Nocturno** (regla física) | El agua que nunca deja de correr de madrugada. En agregados (hotel/DMA), *MNF-trending*: el mínimo nocturno contra su propia línea base | **CONFIRMA** (precisión 1.0 medida en banco de pruebas) |
| **Modelo ML** (LSTM-AE en hogares; forecaster cuantílico LightGBM + CUSUM en agregados) | Desviaciones sostenidas del patrón aprendido, condicionadas a calendario/ocupación/temperatura | **AMPLÍA** cobertura (cola de sospechas) |

Niveles de alerta: `CONFIRMADA` (aviso automático por email/webhook) ·
`SOSPECHA` (cola de revisión) · `OK`.

**Transparencia radical**: cada versión se evalúa contra escenarios de fuga
etiquetados sobre instalaciones que el modelo nunca vio, y la vista *Sistema*
de la consola muestra en vivo el modelo desplegado, su umbral, su origen y
las métricas de la última evaluación. Métricas actuales (banco de pruebas
sintético, día-nivel, instalaciones no vistas): alertas confirmadas con
**precisión 1.0**, cobertura del **92% de hogares con fuga** (ensemble), 6/7
instalaciones agregadas con fuga detectadas.

## La consola

Tres vistas sobre React + FastAPI:

- **Operaciones** — KPIs de flota, tendencias de red y cola de intervención
  priorizada por pérdida estimada en €.
- **Vista Hogar** — lo que ve el usuario final en la app white-label:
  consumo, factura estimada por tarifa regional, alertas explicadas y
  asistente en lenguaje natural (LLM).
- **Sistema** — trazabilidad completa para la due diligence técnica.

## Arranque rápido (demo local)

Requisitos: Python 3.11 (conda recomendado), Node 20+.

```bash
# Backend
cd backend
conda create -n swm python=3.11 && conda activate swm
pip install -r requirements.txt
python -m app.simulators.water_compsumption_simulator   # genera el dataset demo
uvicorn app.api.router:app --reload                     # http://localhost:8000/docs

# Frontend (otra terminal)
cd frontend && npm install && npm run dev               # http://localhost:5173
```

Con Docker: `cp backend/.env.example backend/.env` → `docker compose up -d --build`.

## Conectar un contador real (kit de piloto)

1. Crea el cliente y sus credenciales:
   ```bash
   python -m app.core.tenants create --id hotel_costa --name "Hotel Costa" --email ops@cliente.com
   ```
2. El dispositivo/pasarela envía lecturas (intervalo o índice acumulado):
   ```bash
   curl -X POST https://tu-servidor/api/v1/ingest/readings \
     -H "X-API-Key: <api_key_del_tenant>" -H "Content-Type: application/json" \
     -d '{"meter_id":"hotel_costa_general","value_type":"cumulative",
          "readings":[{"timestamp":"2026-07-06T10:00:00","value":184230}]}'
   ```
   También hay ingesta CSV: `POST /api/v1/ingest/csv` (exports de plataformas AMI).
3. El contador aparece en la consola del tenant y entra en el ciclo nocturno.

**Operación** (crontab del servidor):

```cron
15 6 * * *  python -m app.jobs.nightly          # re-análisis + alertas
0  8 * * 1  python -m app.jobs.weekly_report    # informe semanal por tenant
30 5 * * *  scripts/backup.sh /ruta/backups     # backup con rotación 14 días
```

Monitorización de uptime: apunta UptimeRobot (o similar) a `GET /health`.

## Estructura

```
backend/
├── app/api/          # FastAPI: consola, ingesta, auth multi-tenant, /health
├── app/services/     # detección (detector, night_flow, fleet), alertas, LLM
├── app/ml/           # entrenamiento limpio, forecaster+CUSUM, evaluaciones
├── app/jobs/         # nightly (scoring+alertas) y weekly_report
├── app/simulators/   # bancos de prueba: hogares y contadores agregados
└── scripts/          # backup.sh
frontend/             # consola React (Operaciones / Hogar / Sistema)
landing/              # página de producto (estática, self-contained)
docs/                 # go-to-market, propuesta de piloto, playbook recalibración
legal/                # plantillas ToS, DPA y notas RGPD/DPIA
```

## Reentrenamiento

- Forecaster de agregados: `python -m app.ml.forecaster` (~1 min, CPU).
- LSTM de hogares: `app/ml/kaggle_train_clean.ipynb` (GPU gratuita de Kaggle).
- Procedimiento completo de validación y despliegue:
  [`docs/PLAYBOOK_RECALIBRACION.md`](docs/PLAYBOOK_RECALIBRACION.md).

## Origen y licencia

Nacido como Trabajo de Fin de Máster (UOC, Smart Cities) de
**Álvaro Soto** y evolucionado a producto. Licencia MIT.

📫 asotobarja@gmail.com
