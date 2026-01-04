from openai import OpenAI
from app.core.simulation_config import settings

class LLMAdvisorService:
    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            print("⚠️ AVISO: No se ha configurado OPENAI_API_KEY.")

    def generate_report(self, household_id: str, leak_data: dict, kpis: dict, benchmark: dict) -> str:
        if not self.client:
            return "Asistente desactivado: Configura la API Key."

        # 1. Extraer datos de la Fuga (Fechas y Duración)
        is_leak = leak_data.get("is_leak_detected", False)
        leak_period = leak_data.get("leak_period", {})
        start_date = leak_period.get("start", "N/A")
        end_date = leak_period.get("end", "N/A")
        
        # 2. Extraer Precio del Agua (Para que la IA calcule el despilfarro)
        try:
            water_price = kpis['monthly_bill_estimate']['breakdown']['region_price_m3']
        except:
            water_price = 1.92 # Valor por defecto si falla la estructura

        # 3. Construcción del Estado
        if is_leak:
            leak_status = (
                f"CRÍTICO: Fuga Activa Detectada.\n"
                f"- Periodo afectado: Del {start_date} al {end_date}.\n"
                f"- Intensidad: El {leak_data.get('percentage_anomalies', 0)}% de las lecturas en este periodo son anómalas."
            )
        else:
            leak_status = "El sistema funciona con normalidad. No hay fugas activas."

        horas_anomalas = leak_data.get('leak_details', {}).get('duration_hours', 0)
        coste_estimado_fuga = round(horas_anomalas * 72 * (water_price / 1000), 2) # 72L/h * precio m3

        # 4. El Prompt Maestro
        prompt = f"""
        Actúa como un ingeniero experto en eficiencia hídrica. Analiza los datos de telelectura del hogar {household_id} y genera un informe ejecutivo.

        --- DATOS TÉCNICOS ---
        1. DIAGNÓSTICO IA:
           - Estado: {leak_status}
           - Severidad: Se han detectado anomalías en el {leak_data.get('percentage_anomalies', 0)}% de las lecturas.
           - Duración acumulada real de la anomalía: {horas_anomalas} horas (esto no es la duración total, sino la suma de momentos críticos).
        
        2. ECONOMÍA:
           - Factura mensual promedio: {kpis['monthly_bill_estimate']['total_bill_eur']} €.
           - Precio agua: {water_price} €/m3.
           - ESTIMACIÓN DE PÉRDIDA: Basado en las horas anómalas, se estima un sobrecoste acumulado de aprox. {coste_estimado_fuga} € debido a la ineficiencia.

        3. CONTEXTO SOCIAL:
           - El usuario gasta más agua que el {benchmark['percentile']}% de sus vecinos.
           - Clasificación: {benchmark['status']}.

        --- INSTRUCCIONES DE RESPUESTA (Formato Estricto) ---
        
        **Diagnóstico**
        [Si hay fuga: Indica las fechas ({start_date} a {end_date}) y aclara si es "Puntual" (pocas horas) o "Recurrente" (muchas horas). Si no hay fuga: Felicita por la normalidad. Usa emojis 🔍/✅]

        **Impacto Económico**
        [Analiza la factura. Si hay fuga: Mencia explícitamente los {coste_estimado_fuga} € estimados de pérdida y cómo afecta a su clasificación vecinal. Usa emojis 💶]

        **Consejo de Acción**
        [Si hay fuga recurrente: Sugiere revisar cisternas o riego automático. Si es puntual: Sugiere revisar si se dejaron un grifo abierto. Si no hay fuga pero es derrochador: Sugiere duchas cortas o aireadores. Usa emojis 🛠️/🌿]

        Tono: Profesional, técnico pero accesible. Máximo 130 palabras. No inventes datos que no estén aquí.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Eres un asistente experto en gestión de agua y ahorro."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=400
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"Error OpenAI: {e}")
            return "El asistente está reiniciando sus sistemas (Error de conexión)."

advisor_service = LLMAdvisorService()