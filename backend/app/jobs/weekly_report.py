"""
Informe SEMANAL por email, por tenant. El entregable que mantiene vivo el
piloto: el responsable lo reenvía a su jefe cada lunes.

Programar:
    0 8 * * 1  cd /ruta/al/backend && /ruta/python -m app.jobs.weekly_report >> /var/log/swm_weekly.log 2>&1

Requiere SMTP configurado en .env (si no, imprime el informe por consola —
útil para revisarlo antes de activar el envío).
"""
from datetime import datetime, timedelta

import pandas as pd

from app.core.simulation_config import settings
from app.core.tenants import load_tenants, OPEN_MODE_TENANT
from app.core.water_prices import REGIONAL_PRICES
from app.repository.data_loader import data_loader
from app.services.alerting import alert_service
from app.services.fleet import fleet_service


def build_report(tenant: dict, region: str = "Promedio Nacional") -> str:
    overview = fleet_service.get_overview(region, tenant)
    k = overview["kpis"]
    alerts = [h for h in overview["households"] if h["alert_level"] != "OK"]

    # Consumo de los últimos 7 días de los contadores del tenant
    week_liters = 0.0
    cutoff = None
    for hid in data_loader.get_all_household_ids(tenant):
        try:
            df = data_loader.get_household_data(hid)
        except ValueError:
            continue
        if cutoff is None:
            cutoff = df["timestamp"].max() - timedelta(days=7)
        week_liters += float(df.loc[df["timestamp"] >= cutoff, "consumption_l"].sum())

    price = REGIONAL_PRICES.get(region, 1.92)
    lines = [
        f"INFORME SEMANAL — {tenant['name']}",
        f"Generado: {datetime.now().strftime('%d/%m/%Y')}",
        "=" * 46,
        "",
        f"Consumo últimos 7 días: {week_liters/1000:,.1f} m³ (≈ {week_liters/1000*price:,.0f} €)",
        f"Contadores monitorizados: {k['households_scored']}/{k['households_total']}",
        f"Alertas activas: {k['active_alerts']} "
        f"({k.get('confirmed_alerts', 0)} confirmadas · {k.get('suspected_alerts', 0)} sospechas)",
        f"Pérdida estimada por fugas: {k['estimated_loss_l']/1000:,.1f} m³ ≈ {k['estimated_loss_eur']:,.0f} €",
        "",
    ]
    if alerts:
        lines.append("REQUIEREN ATENCIÓN:")
        for h in alerts[:10]:
            lines.append(
                f"  · {h['household_id']} [{h['alert_level']}] — "
                f"pérdida est. {h['estimated_loss_l']:,.0f} L"
            )
    else:
        lines.append("✓ Sin fugas activas esta semana.")
    lines += ["", "Detalle completo en la consola de operaciones.", "— Smart Water Monitor"]
    return "\n".join(lines)


def main():
    tenants = load_tenants() or [OPEN_MODE_TENANT]
    for tenant in tenants:
        report = build_report(tenant)
        email = tenant.get("report_email", "")
        print(f"\n{report}\n")
        if email and settings.SMTP_HOST:
            # Reutiliza el canal SMTP del servicio de alertas
            original_to = settings.ALERT_EMAIL_TO
            settings.ALERT_EMAIL_TO = email
            ok = alert_service._send_email(
                f"📊 Informe semanal de agua — {tenant['name']}", report
            )
            settings.ALERT_EMAIL_TO = original_to
            print(f"[WEEKLY] {tenant['id']} → {email}: {'enviado' if ok else 'FALLO'}")
        else:
            print(f"[WEEKLY] {tenant['id']}: sin email/SMTP configurado (solo consola)")


if __name__ == "__main__":
    main()
