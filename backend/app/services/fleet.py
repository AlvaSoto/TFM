"""
Servicio de flota: la vista de la GESTORA (el comprador del producto).

Puntúa todos los hogares con el detector, persiste los resultados en disco
(data/fleet_scores.json) y agrega los KPIs que necesita un responsable de
operaciones/clientes: cuántas alertas activas hay, cuánta agua se está
perdiendo y cuánto dinero supone en la tarifa de su región.

La estimación de pérdida NO usa un caudal fijo inventado: se calcula como el
exceso de consumo de los días anómalos sobre la mediana de los días normales
del propio hogar (su línea base real).

Precomputar toda la flota (tarda: ejecuta el modelo sobre cada hogar):
    python -m app.services.fleet
"""
import json
import time

import pandas as pd

from app.core.simulation_config import settings
from app.core.water_prices import REGIONAL_PRICES
from app.repository.data_loader import data_loader
from app.services.detector import detector_service
from app.services.night_flow import mnf_analysis, combine_alert_level
from app.core.profiles import parse_profile

CACHE_PATH = settings.BASE_DIR / "data" / "fleet_scores.json"

# Versión del esquema del resumen por hogar. Si una entrada cacheada no la
# tiene (o es antigua), se vuelve a puntuar ese hogar.
SCHEMA_VERSION = 2


class FleetService:
    def __init__(self):
        self._scores = {}
        self._trends_cache = None
        if CACHE_PATH.exists():
            try:
                self._scores = json.loads(CACHE_PATH.read_text())
                print(f"Fleet cache loaded: {len(self._scores)} households scored")
            except Exception as e:
                print(f"Could not read fleet cache ({e}), starting empty")

    # ------------------------------------------------------------------
    # Estimación de pérdida basada en datos (sustituye al 72 L/h fijo)
    # ------------------------------------------------------------------
    def estimate_loss_liters(self, df: pd.DataFrame, anomalous_days: list) -> float:
        """
        Pérdida estimada = suma, en los días anómalos, del exceso de consumo
        sobre la mediana de los días normales del propio hogar.
        """
        if not anomalous_days:
            return 0.0
        daily = df.set_index("timestamp")["consumption_l"].resample("D").sum()
        day_keys = daily.index.strftime("%Y-%m-%d")
        anom = set(anomalous_days)
        is_anom = day_keys.isin(anom)

        normal_days = daily[~is_anom]
        baseline = float(normal_days.median()) if len(normal_days) else float(daily.median())

        excess = (daily[is_anom] - baseline).clip(lower=0).sum()
        return round(float(excess), 1)

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------
    def score_household(self, household_id: str, force: bool = False) -> dict:
        cached = self._scores.get(household_id)
        if not force and cached and cached.get("schema") == SCHEMA_VERSION:
            return cached

        df = data_loader.get_household_data(household_id)
        analysis = detector_service.analyse_household(df)

        if "error" in analysis:
            summary = {"household_id": household_id, "error": analysis["error"], "schema": SCHEMA_VERSION}
        else:
            loss_l = self.estimate_loss_liters(df, analysis["anomalous_days"])
            daily_avg = df.set_index("timestamp")["consumption_l"].resample("D").sum().mean()

            # Ensemble: la regla física MNF confirma (o cuestiona) al modelo ML
            mnf = mnf_analysis(df)
            alert_level = combine_alert_level(analysis["is_leak_detected"], mnf["mnf_alert"])

            summary = {
                "household_id": household_id,
                "schema": SCHEMA_VERSION,
                # --- ML (LSTM Autoencoder) ---
                "is_leak_detected": analysis["is_leak_detected"],
                "anomalies_detected": analysis["anomalies_detected"],
                "percentage_anomalies": analysis["percentage_anomalies"],
                "anomalous_days": analysis["anomalous_days"],
                "anomalous_days_count": len(analysis["anomalous_days"]),
                "leak_period": analysis["leak_period"],
                "worst_date": analysis["leak_details"].get("worst_date"),
                # --- Regla MNF (confirmación física) ---
                "mnf_alert": mnf["mnf_alert"],
                "mnf_days": mnf["mnf_days"],
                "mnf_days_count": len(mnf["mnf_days"]),
                "max_night_floor_l": mnf["max_night_floor_l"],
                # --- Ensemble ---
                "alert_level": alert_level,
                # --- Impacto ---
                "estimated_loss_l": loss_l,
                "daily_avg_l": round(float(daily_avg), 1),
                "scored_at": time.strftime("%Y-%m-%d %H:%M"),
            }

        # Alerta saliente al TRANSICIONAR a CONFIRMADA (no en re-scorings repetidos)
        prev_level = (cached or {}).get("alert_level")
        if summary.get("alert_level") == "CONFIRMADA" and prev_level != "CONFIRMADA":
            try:
                from app.services.alerting import alert_service
                alert_service.notify_confirmed_leak(summary)
            except Exception as e:
                print(f"[ALERT] fallo no bloqueante: {e}")

        self._scores[household_id] = summary
        self._trends_cache = None  # los agregados de red dependen de los scores
        return summary

    def save(self):
        CACHE_PATH.write_text(json.dumps(self._scores, indent=1))

    def pending_ids(self) -> list:
        return [
            h for h in data_loader.get_all_household_ids()
            if self._scores.get(h, {}).get("schema") != SCHEMA_VERSION
        ]

    def score_batch(self, limit: int = 10) -> int:
        """Puntúa hasta `limit` hogares pendientes y persiste. Devuelve cuántos puntuó."""
        pending = self.pending_ids()[:limit]
        for i, hid in enumerate(pending):
            print(f"Scoring {hid} ({i + 1}/{len(pending)})...")
            self.score_household(hid)
            if (i + 1) % 5 == 0:
                self.save()
        self.save()
        return len(pending)

    # ------------------------------------------------------------------
    # Tendencias de red: consumo agregado diario + hogares en alerta/día
    # ------------------------------------------------------------------
    def get_trends(self) -> dict:
        if self._trends_cache is not None:
            return self._trends_cache

        daily = data_loader.df.set_index("timestamp")["consumption_l"].resample("D").sum() / 1000.0
        labels = daily.index.strftime("%Y-%m-%d").tolist()

        alert_counts: dict = {}
        for s in self._scores.values():
            if s.get("schema") == SCHEMA_VERSION and "error" not in s:
                for d in s.get("anomalous_days", []):
                    alert_counts[d] = alert_counts.get(d, 0) + 1

        self._trends_cache = {
            "labels": labels,
            "network_m3": [round(float(v), 1) for v in daily.tolist()],
            "households_in_alert": [alert_counts.get(d, 0) for d in labels],
        }
        return self._trends_cache

    # ------------------------------------------------------------------
    # Vista agregada para la gestora
    # ------------------------------------------------------------------
    def get_overview(self, region: str = "Promedio Nacional") -> dict:
        price = REGIONAL_PRICES.get(region, REGIONAL_PRICES["Promedio Nacional"])
        all_ids = data_loader.get_all_household_ids()

        rows = []
        for hid in all_ids:
            s = self._scores.get(hid)
            if s and "error" not in s and s.get("schema") == SCHEMA_VERSION:
                rows.append({
                    **s,
                    "estimated_loss_eur": round(s["estimated_loss_l"] / 1000 * price, 2),
                    "profile": parse_profile(hid),
                })

        confirmed = [r for r in rows if r["alert_level"] == "CONFIRMADA"]
        suspected = [r for r in rows if r["alert_level"] == "SOSPECHA"]
        alerts = confirmed + suspected
        total_loss_l = sum(r["estimated_loss_l"] for r in alerts)

        # Confirmadas primero, luego sospechas, dentro de cada nivel por pérdida estimada
        level_rank = {"CONFIRMADA": 0, "SOSPECHA": 1, "OK": 2}
        rows.sort(key=lambda r: (level_rank[r["alert_level"]], -r["estimated_loss_l"], -r["percentage_anomalies"]))

        return {
            "kpis": {
                "households_total": len(all_ids),
                "households_scored": len(rows),
                "households_pending": len(all_ids) - len(rows),
                "active_alerts": len(alerts),
                "confirmed_alerts": len(confirmed),
                "suspected_alerts": len(suspected),
                "estimated_loss_l": round(total_loss_l, 0),
                "estimated_loss_eur": round(total_loss_l / 1000 * price, 2),
                "region": region,
                "price_per_m3": price,
            },
            "households": rows,
        }


fleet_service = FleetService()


if __name__ == "__main__":
    print("Precomputando el scoring de toda la flota...")
    n = fleet_service.score_batch(limit=10_000)
    print(f"Hecho: {n} hogares puntuados. Cache en {CACHE_PATH}")
