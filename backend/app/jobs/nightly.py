"""
Job NOCTURNO: re-analiza los contadores reales con datos nuevos y dispara
las alertas de transición a CONFIRMADA. Es lo que convierte la herramienta
en "monitorización continua".

Programar (crontab -e en el servidor del piloto):
    15 6 * * *  cd /ruta/al/backend && /ruta/python -m app.jobs.nightly >> /var/log/swm_nightly.log 2>&1

(a las 06:15, tras cerrar la madrugada — la ventana que analiza el MNF)
En Docker: añade un servicio con `command: python -m app.jobs.nightly` y un
scheduler externo (cron del host u Ofelia).
"""
import time

from app.repository.readings_store import readings_store
from app.services.fleet import fleet_service


def main():
    t0 = time.time()
    pilot_meters = readings_store.meter_ids()
    print(f"[NIGHTLY] {len(pilot_meters)} contadores reales para re-analizar")

    for i, meter_id in enumerate(pilot_meters):
        # force=True: cada noche se re-evalúa con todas las lecturas acumuladas.
        # La transición a CONFIRMADA dispara la alerta (email/webhook) desde fleet.
        try:
            summary = fleet_service.score_household(meter_id, force=True)
            level = summary.get("alert_level", "?")
            print(f"[NIGHTLY] {i+1}/{len(pilot_meters)} {meter_id}: {level}")
        except Exception as e:
            print(f"[NIGHTLY] ERROR en {meter_id}: {e}")

    # Los contadores demo solo se puntúan si nunca lo fueron (no cambian)
    pending_demo = [m for m in fleet_service.pending_ids() if m not in pilot_meters]
    if pending_demo:
        print(f"[NIGHTLY] {len(pending_demo)} contadores demo pendientes; puntuando...")
        fleet_service.score_batch(limit=len(pending_demo))

    fleet_service.save()
    print(f"[NIGHTLY] Completado en {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
