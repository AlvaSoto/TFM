"""
Alertas salientes del piloto: nadie mira un dashboard a las 3 AM.

Cuando un contador pasa a nivel CONFIRMADA, se notifica por los canales
configurados (todos opcionales, vía variables de entorno):
  - Email SMTP  (SMTP_HOST/PORT/USER/PASSWORD, ALERT_EMAIL_FROM/TO)
  - Webhook     (ALERT_WEBHOOK_URL: POST JSON — vale para Slack/Teams/n8n/Zapier)

Sin configuración, las alertas se registran en el log del servidor y no se
pierde nada: el estado vive en fleet_scores.json.
"""
import json
import smtplib
import urllib.request
from email.mime.text import MIMEText

from app.core.simulation_config import settings


class AlertService:
    def notify_confirmed_leak(self, summary: dict, region_price_m3: float = 1.92) -> dict:
        meter = summary["household_id"]
        loss_l = summary.get("estimated_loss_l", 0)
        loss_eur = round(loss_l / 1000 * region_price_m3, 2)
        period = summary.get("leak_period") or {}

        subject = f"💧 FUGA CONFIRMADA — {meter}"
        body = (
            f"Smart Water Monitor ha CONFIRMADO una fuga.\n\n"
            f"Contador: {meter}\n"
            f"Periodo afectado: {period.get('start', '—')} → {period.get('end', '—')}\n"
            f"Noches con caudal continuo: {summary.get('mnf_days_count', 0)} "
            f"(suelo máx. {summary.get('max_night_floor_l', 0)} L/15min)\n"
            f"Pérdida estimada: {loss_l:,.0f} L (≈ {loss_eur} €)\n\n"
            f"Detalle en la consola: vista Operaciones → {meter}\n"
        )

        sent = {"email": False, "webhook": False}
        sent["email"] = self._send_email(subject, body)
        sent["webhook"] = self._send_webhook({
            "event": "leak_confirmed",
            "meter_id": meter,
            "estimated_loss_l": loss_l,
            "estimated_loss_eur": loss_eur,
            "leak_period": period,
            "text": subject,
        })
        print(f"[ALERT] {subject} | email={sent['email']} webhook={sent['webhook']}")
        return sent

    # ------------------------------------------------------------------
    def _send_email(self, subject: str, body: str) -> bool:
        if not (settings.SMTP_HOST and settings.ALERT_EMAIL_FROM and settings.ALERT_EMAIL_TO):
            return False
        try:
            msg = MIMEText(body, "plain", "utf-8")
            msg["Subject"] = subject
            msg["From"] = settings.ALERT_EMAIL_FROM
            msg["To"] = settings.ALERT_EMAIL_TO
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as s:
                s.starttls()
                if settings.SMTP_USER:
                    s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                s.send_message(msg)
            return True
        except Exception as e:
            print(f"[ALERT] Error enviando email: {e}")
            return False

    def _send_webhook(self, payload: dict) -> bool:
        if not settings.ALERT_WEBHOOK_URL:
            return False
        try:
            req = urllib.request.Request(
                settings.ALERT_WEBHOOK_URL,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                return 200 <= resp.status < 300
        except Exception as e:
            print(f"[ALERT] Error enviando webhook: {e}")
            return False


alert_service = AlertService()
