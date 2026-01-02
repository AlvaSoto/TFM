import pandas as pd
import numpy as np
from app.core.water_prices import REGIONAL_PRICES, FIXED_MONTHLY_FEE

class ConsumptionService:
    
    def __init__(self):
        self.default_region = "Promedio Nacional"

    
    def _calculate_bill(self, total_filters: float, region: str = None) -> dict:
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
        # 3. Adding fixed monthly fee
        total_cost = variable_cost + FIXED_MONTHLY_FEE

        # 4. Taxes (IVA 10%)
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

    def get_household_kpis(self, df: pd.DataFrame, region: str = None) -> dict:
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
            "data_range_days": total_days
        }
    
consumption_service = ConsumptionService()