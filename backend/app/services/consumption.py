import pandas as pd
import numpy as np
from app.core.water_prices import REGIONAL_PRICES, FIXED_MONTHLY_FEE

from typing import List, Dict, Optional

class ConsumptionService:
    
    def __init__(self):
        self.default_region = "Promedio Nacional"

    
    def _calculate_bill(self, total_filters: float, region: Optional[str] = None) -> dict:
        """
        Calculate the water bill based on total consumption in liters and region.
        """
        if region is None or region not in REGIONAL_PRICES:
            region = self.default_region
        
        price_per_m3 = REGIONAL_PRICES[region]
        # 1. Convert liters to cubic meters
        total_m3 = total_filters / 1000.0
        # 2. Calculate cost variable (Unit price * consumption)
        # I am using the regional price per cubic meter which includes supply and sanitation
        variable_cost = total_m3 * price_per_m3
        # 3. Fixed monthly fee + taxes (IVA 10%)
        subtotal = variable_cost + FIXED_MONTHLY_FEE
        taxes = subtotal * 0.10
        total_cost = subtotal + taxes

        
        return {
            "region": region,
            "total_bill_eur": round(total_cost, 2),
            "breakdown": {
                "consumption_m3": round(total_m3, 3),
                "region_price_m3": price_per_m3,
                "variable_cost": round(variable_cost, 2),
                "fixed_cost": round(FIXED_MONTHLY_FEE, 2),
                "taxes": round(taxes, 2)
            }
        }
    

    def calculate_monthly_bill_history(self, df: pd.DataFrame, region: str) -> List[Dict]:

        """
        Calculate monthly bill history from consumption data.
        """
        df = df.copy()
        df.set_index("timestamp", inplace=True) # Ensure timestamp is index
        # Grouping by month ME = Month End and summing consumption
        monthly_consumption = df['consumption_l'].resample('ME').sum()

        bill_history = []
        for date, total_liters in monthly_consumption.items():
            # Asegurarse de que date es datetime
            if not hasattr(date, 'strftime'):
                try:
                    date = pd.to_datetime(date)
                except Exception:
                    pass
            bill_data = self._calculate_bill(total_liters, region)
            bill_history.append({
                "month_name": date.strftime("%B-%Y") if hasattr(date, 'strftime') else str(date),
                "month_iso": date.strftime("%Y-%m") if hasattr(date, 'strftime') else str(date),
                "total_liters": round(total_liters, 0),
                "total_bill": bill_data["total_bill_eur"]
            })
        return bill_history[::-1]  # Return in reverse chronological order, most recent first
    
    def get_daily_status(self, df: pd.DataFrame) -> Dict:
        """
        Get today's consumption status compared to yesterday.
        """


        df = df.sort_values("timestamp")

        #Grouping the says
        daily = df.set_index("timestamp")["consumption_l"].resample("D").sum()

        if len(daily) < 2:
            return {"current": 0, "trend": 0}
        
        today_val = daily.iloc[-1]
        yesterday_val = daily.iloc[-2]

        trend = 0
        if yesterday_val > 0:
            trend = ((today_val - yesterday_val) / yesterday_val) * 100
        
        return {
            "date": daily.index[-1].strftime("%d/%m/%Y"),
            "today_l": round(today_val, 1),
            "yesterday_l": round(yesterday_val, 1),
            "trend_percent": round(trend, 1),
            "status": "Ahorrando" if trend < 0 else "Gastando Más"
        }


    def get_household_kpis(self, df: pd.DataFrame, region: str = "Promedio Nacional") -> dict:
        """
        Calculate key performance indicators for a household's water consumption.
        """

        df = df.sort_values("timestamp")

        total_consumption_l = df['consumption_l'].sum()
        total_days = (df['timestamp'].max() - df['timestamp'].min()).days 

        if total_days < 1: total_days = 1  # Avoid division by zero

        daily_avg_l = total_consumption_l / total_days

        monthly_projection_l = daily_avg_l * 30

        #Bill calculaiton
        bill_data = self._calculate_bill(monthly_projection_l, region)

        last_date = df['timestamp'].max()
        current_week_start = last_date - pd.Timedelta(days=7)
        prev_week_start = current_week_start - pd.Timedelta(days=7)

        current_week_consumption = df[(df['timestamp'] >= current_week_start) & (df['timestamp'] < last_date)]['consumption_l'].sum()
        prev_week_consumption = df[(df['timestamp'] >= prev_week_start) & (df['timestamp'] < current_week_start)]['consumption_l'].sum()

        current_month_name = last_date.strftime("%B %Y")

        trend_percent = 0
        if prev_week_consumption > 0:
            trend_percent = ((current_week_consumption - prev_week_consumption) / prev_week_consumption) * 100

        return {
            "total_consumption_l": round(total_consumption_l, 2),
            "daily_average_l": round(daily_avg_l, 2),
            "monthly_bill_estimate": bill_data,
            "weekly_trend_percent": round(trend_percent, 2),
            "region_used": region,
            "trend_vs_last_week": round(trend_percent, 1),
            "data_range_days": total_days,
            "current_month": current_month_name
        }
    
    def get_consumption_history(self, df: pd.DataFrame, period: str = "daily") -> dict:
        df_chart = df.copy()
        df_chart.set_index("timestamp", inplace=True)

        if period == "weekly":
            resampled = df_chart['consumption_l'].resample('W').sum()
            format_str = "%Y-%U"
        elif period == "monthly":
            resampled = df_chart['consumption_l'].resample('ME').sum() # 'ME' es el nuevo alias para Month End en pandas reciente
            format_str = "%Y-%m"
        else:  # daily
            resampled = df_chart['consumption_l'].resample('D').sum()
            format_str = "%Y-%m-%d"

        # --- CORRECCIÓN CLAVE ---
        # 1. Asegurar que redondeamos usando numpy de forma explícita
        values_rounded = np.round(resampled.to_numpy(), 1).tolist()
        # 2. Formatear fechas de manera segura
        if hasattr(resampled.index, 'strftime'):
            labels = resampled.index.strftime(format_str).tolist()
        else:
            try:
                labels = pd.to_datetime(resampled.index).strftime(format_str).tolist()
            except Exception:
                labels = [str(x) for x in resampled.index]
        return {
            "labels": labels,
            "values": values_rounded
        }
    
    def get_hourly_patterns(self, df: pd.DataFrame) -> dict:
        df_patterns = df.copy()
        
        # Asegurar que timestamp es datetime
        if not pd.api.types.is_datetime64_any_dtype(df_patterns['timestamp']):
             df_patterns['timestamp'] = pd.to_datetime(df_patterns['timestamp'])

        df_patterns['hour'] = df_patterns['timestamp'].dt.hour
        hourly_avg = df_patterns.groupby('hour')['consumption_l'].mean()

        # Reindexar
        hourly_avg = hourly_avg.reindex(range(24), fill_value=0.0)

        # --- CORRECCIÓN CLAVE ---
        # Usar np.round explícitamente sobre los valores
        values_rounded = np.round(hourly_avg.to_numpy(), 2).tolist()

        return {
            "hours": list(range(24)),
            "average_consumption": values_rounded,
            "peak_hour": int(hourly_avg.idxmax()),
        }
    

    def get_community_comparison(self, household_df: pd.DataFrame, all_households_df: pd.DataFrame) -> dict:
        """
        Benchmarking: Compara el consumo diario de esta casa con la media de TODAS las casas.
        Calcula un percentil para decirle al usuario si es eficiente o derrochador.
        """
        # 1. Calcular la media diaria de ESTA casa
        my_total = household_df["consumption_l"].sum()
        my_days = (household_df["timestamp"].max() - household_df["timestamp"].min()).days
        if my_days < 1: my_days = 1
        my_daily_avg = my_total / my_days
        
        # 2. Calcular la media diaria de CADA casa de la comunidad (Dataset completo)
        # Agrupamos por ID y sumamos todo su consumo
        community_totals = all_households_df.groupby("household_id")["consumption_l"].sum()
        
        # Asumimos que todas tienen el mismo rango de días (aprox) para simplificar el cálculo masivo
        # Dividimos el total de cada casa entre los días aproximados del dataset (ej: 180)
        total_days_comm = (all_households_df["timestamp"].max() - all_households_df["timestamp"].min()).days
        if total_days_comm < 1: total_days_comm = 1
        
        # Esto nos da una lista con la media diaria de los 160 vecinos
        community_daily_avgs = community_totals / total_days_comm
        
        # 3. Calcular la media global (El promedio del barrio)
        avg_community_consumption = community_daily_avgs.mean()
        
        # 4. Calcular el Percentil (Ranking)
        # ¿Qué porcentaje de vecinos gasta MENOS que yo?
        # Si tengo un percentil 90, significa que gasto más que el 90% de la gente (soy derrochador).
        percentile = (community_daily_avgs < my_daily_avg).mean() * 100
        
        # 5. Definir estatus
        status = "Eficiente"
        if percentile > 75: status = "Derrochador" # Estás en el top 25% de gasto
        elif percentile > 50: status = "Promedio"  # Estás por encima de la media
        
        return {
            "my_daily_avg": round(my_daily_avg, 1),
            "community_daily_avg": round(avg_community_consumption, 1),
            "percentile": round(percentile, 0), 
            "status": status
        }

    
consumption_service = ConsumptionService()