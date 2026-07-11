"""
Simulador de CONTADORES AGREGADOS: hoteles/balnearios y pueblos/sectores (DMA).

A diferencia del simulador de hogares (eventos discretos), aquí el consumo se
modela como CURVAS DE CAUDAL por componente moduladas por covariables
(ocupación, estacionalidad, día de la semana) más ruido estocástico. Es lo
apropiado para contadores agregados: la suma de muchos usuarios produce curvas
suaves — la varianza relativa cae con ~sqrt(N) — y eso es justamente lo que
explota el enfoque forecast+CUSUM de la Fase B.

Magnitudes calibradas con referencias de la industria:
  - Hotel: 300-450 L por habitación-noche ocupada (rango habitual 200-600),
    repartidos entre habitaciones, lavandería, cocina, piscina y riego.
  - Pueblo/DMA: ~280 L/vivienda/día (dotación doméstica típica en España
    ~130 L/persona/día × 2.2 personas) + pérdidas de fondo de red (5-12%).

Claves del realismo para los detectores:
  - El mínimo nocturno de un hotel/pueblo NUNCA es cero (lavandería nocturna,
    riego, pérdidas de fondo) → la regla MNF absoluta de hogares no sirve;
    hace falta MNF-trending (mínimo nocturno vs su propia línea base).
  - Las fugas se inyectan como escalón de caudal proporcional a la escala del
    contador (3-15% del caudal medio), 24h-7días, 20% intermitentes.

Salidas (backend/data/):
  - aggregated_meters_dataset.csv    → timestamp, consumption_l, is_leak, household_id
    (mismas columnas que el dataset de hogares: todo el pipeline es reutilizable)
  - aggregated_meters_covariates.csv → household_id, date, occupancy, temp_c,
    meter_type, units (features exógenas para el forecaster de la Fase B)

Uso (desde backend/):  python -m app.simulators.aggregated_meter_simulator
"""
import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

RESOLUTION_MIN = 15
STEPS_PER_DAY = 24 * 60 // RESOLUTION_MIN  # 96

AGG_CONFIG = {
    "simulation_days": 180,
    "n_hotels": 30,
    "n_pueblos": 20,
    "leak_probability": 0.6,          # fracción de contadores con alguna fuga
    "leaks_per_meter_mean": 1.2,      # Poisson
    "leak_flow_fraction": (0.03, 0.15),  # caudal de fuga como % del caudal medio
    "leak_duration_hours": (24, 168), # 1-7 días
    "leak_intermittent_probability": 0.2,
    "seed": 7,
}


# ----------------------------------------------------------------------
# Curvas horarias base (fracción del volumen diario por hora; suman 1.0)
# ----------------------------------------------------------------------
def _norm(a):
    a = np.asarray(a, dtype=float)
    return a / a.sum()

# Habitaciones de hotel: pico fuerte de mañana (duchas 7-10h), pico de noche
HOTEL_ROOMS_HOURLY = _norm([
    0.5, 0.3, 0.2, 0.2, 0.3, 1.0, 3.5, 7.0, 8.5, 6.0,   # 00-09
    3.0, 2.0, 2.0, 2.5, 2.0, 1.5, 2.0, 3.0, 4.5, 6.0,   # 10-19
    7.0, 6.5, 4.0, 1.5,                                  # 20-23
])
# Lavandería: turno de mañana + refuerzo nocturno (tarifa valle)
HOTEL_LAUNDRY_HOURLY = _norm([
    1.0, 2.0, 2.0, 1.0, 0.2, 0.2, 0.5, 1.0, 3.0, 5.0,
    5.0, 4.0, 3.0, 2.0, 1.0, 0.5, 0.3, 0.2, 0.2, 0.2,
    0.3, 0.5, 0.8, 1.0,
])
# Cocina: tres picos de servicio
HOTEL_KITCHEN_HOURLY = _norm([
    0.1, 0.1, 0.1, 0.1, 0.2, 0.5, 2.0, 4.0, 3.0, 1.0,
    1.0, 2.5, 5.0, 5.0, 2.5, 0.8, 0.5, 0.8, 2.0, 4.0,
    4.5, 2.5, 1.0, 0.3,
])
# Piscina/spa: llenados y contralavados de mañana
HOTEL_POOL_HOURLY = _norm([
    0.5, 0.5, 0.5, 0.5, 1.0, 2.0, 5.0, 6.0, 5.0, 3.0,
    2.0, 1.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
    1.0, 1.0, 0.8, 0.5,
])
# Riego: nocturno
IRRIGATION_HOURLY = _norm([
    2.0, 3.0, 3.0, 2.0, 1.0, 0.5, 0.1, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    0.5, 1.5, 2.5, 3.0,
])
# Doméstico agregado (pueblo): mañana, mediodía y noche
PUEBLO_DOMESTIC_HOURLY = _norm([
    0.6, 0.4, 0.3, 0.3, 0.4, 1.0, 2.5, 5.0, 6.5, 5.5,
    4.5, 4.5, 5.0, 5.5, 5.0, 4.0, 3.5, 3.5, 4.0, 5.0,
    5.5, 5.0, 3.5, 1.5,
])


def _hourly_to_steps(hourly_fractions: np.ndarray) -> np.ndarray:
    """Curva de 24 fracciones/hora → 96 fracciones por paso de 15 min."""
    return np.repeat(hourly_fractions / (60 / RESOLUTION_MIN), 60 // RESOLUTION_MIN)


def _seasonal_temperature(days: int, start: datetime, rng) -> np.ndarray:
    """Temperatura media diaria sintética (España): seno anual 10-30ºC + ruido."""
    doy = np.array([(start + timedelta(days=i)).timetuple().tm_yday for i in range(days)])
    base = 20 + 10 * np.sin(2 * np.pi * (doy - 105) / 365)  # pico ~mediados de julio
    return base + rng.normal(0, 1.5, days)


def _hotel_occupancy(days: int, start: datetime, temps: np.ndarray, rng) -> np.ndarray:
    """
    Ocupación diaria [0.15, 0.98]: estacional (ligada a temperatura), con
    subida de fin de semana y persistencia AR(1) (las reservas no saltan al azar).
    """
    seasonal = 0.35 + 0.5 * (temps - temps.min()) / (temps.max() - temps.min())
    weekend = np.array([
        0.12 if (start + timedelta(days=i)).weekday() >= 4 else 0.0
        for i in range(days)
    ])
    noise = np.zeros(days)
    for i in range(1, days):
        noise[i] = 0.7 * noise[i - 1] + rng.normal(0, 0.05)
    return np.clip(seasonal + weekend + noise, 0.15, 0.98)


# ----------------------------------------------------------------------
# Fugas (escalón de caudal proporcional a la escala del contador)
# ----------------------------------------------------------------------
def _inject_leaks(flow_lpm: np.ndarray, mean_flow_lpm: float, rng, cfg=AGG_CONFIG):
    """Añade fugas al vector de caudal (L/min por paso). Devuelve (flow, is_leak)."""
    is_leak = np.zeros(len(flow_lpm), dtype=int)
    if rng.random() > cfg["leak_probability"]:
        return flow_lpm, is_leak

    n_leaks = max(1, rng.poisson(cfg["leaks_per_meter_mean"]))
    steps_total = len(flow_lpm)
    used = []

    for _ in range(n_leaks):
        frac = rng.uniform(*cfg["leak_flow_fraction"])
        leak_lpm = frac * mean_flow_lpm
        dur_h = rng.uniform(*cfg["leak_duration_hours"])
        dur_steps = int(dur_h * 60 / RESOLUTION_MIN)

        for _attempt in range(50):
            start = rng.integers(0, max(1, steps_total - dur_steps))
            end = start + dur_steps
            if all(end <= s or start >= e for s, e in used):
                used.append((start, end))
                if rng.random() < cfg["leak_intermittent_probability"]:
                    # Intermitente: ciclos 12h on / 12h off
                    cycle = 12 * 60 // RESOLUTION_MIN
                    for cs in range(start, end, 2 * cycle):
                        ce = min(cs + cycle, end)
                        flow_lpm[cs:ce] += leak_lpm
                        is_leak[cs:ce] = 1
                else:
                    flow_lpm[start:end] += leak_lpm
                    is_leak[start:end] = 1
                break

    return flow_lpm, is_leak


# ----------------------------------------------------------------------
# Generadores por tipo de contador
# ----------------------------------------------------------------------
def simulate_hotel(meter_id: str, days: int, start: datetime, rng):
    """Hotel/balneario: componentes modulados por ocupación diaria."""
    rooms = int(rng.integers(40, 140))
    has_pool = rng.random() < 0.6      # balnearios/hoteles con spa o piscina
    has_garden = rng.random() < 0.5

    temps = _seasonal_temperature(days, start, rng)
    occupancy = _hotel_occupancy(days, start, temps, rng)

    liters_per_room_night = rng.uniform(300, 450)
    # Reparto del volumen por habitación-noche entre componentes
    room_share, laundry_share, kitchen_share = 0.62, 0.18, 0.20

    steps = {
        "rooms": _hourly_to_steps(HOTEL_ROOMS_HOURLY),
        "laundry": _hourly_to_steps(HOTEL_LAUNDRY_HOURLY),
        "kitchen": _hourly_to_steps(HOTEL_KITCHEN_HOURLY),
        "pool": _hourly_to_steps(HOTEL_POOL_HOURLY),
        "irrigation": _hourly_to_steps(IRRIGATION_HOURLY),
    }

    daily_liters = np.zeros((days, STEPS_PER_DAY))
    for d in range(days):
        occ_rooms = rooms * occupancy[d]
        vol = occ_rooms * liters_per_room_night
        day_curve = (
            vol * room_share * steps["rooms"]
            + vol * laundry_share * steps["laundry"]   # lavandería del día
            + vol * kitchen_share * steps["kitchen"]
        )
        if has_pool:
            # 2-5 m³/día de reposición+contralavado, más en verano
            pool_vol = rng.uniform(2000, 5000) * (0.6 + 0.4 * (temps[d] > 22))
            day_curve = day_curve + pool_vol * steps["pool"]
        if has_garden and temps[d] > 18:
            irr_vol = rng.uniform(1500, 4000) * min(1.0, (temps[d] - 18) / 8)
            day_curve = day_curve + irr_vol * steps["irrigation"]

        # Ruido multiplicativo suave (la agregación ya suaviza) + rachas
        noise = rng.normal(1.0, 0.08, STEPS_PER_DAY)
        daily_liters[d] = np.maximum(0, day_curve * noise)

    liters = daily_liters.ravel()  # litros por paso de 15 min
    flow_lpm = liters / RESOLUTION_MIN
    mean_flow = float(flow_lpm.mean())
    flow_lpm, is_leak = _inject_leaks(flow_lpm, mean_flow, rng)

    covars = pd.DataFrame({
        "household_id": meter_id,
        "date": [(start + timedelta(days=d)).strftime("%Y-%m-%d") for d in range(days)],
        "occupancy": np.round(occupancy, 3),
        "temp_c": np.round(temps, 1),
        "meter_type": "hotel",
        "units": rooms,
    })
    return flow_lpm * RESOLUTION_MIN, is_leak, covars


def simulate_pueblo(meter_id: str, days: int, start: datetime, rng):
    """
    Pueblo o sector de red (DMA): agregado de N viviendas + pérdidas de fondo.
    La varianza relativa escala ~1/sqrt(N): pueblos grandes = curvas más suaves.
    """
    homes = int(rng.integers(60, 300))
    liters_per_home_day = rng.uniform(240, 320)

    temps = _seasonal_temperature(days, start, rng)
    dom_steps = _hourly_to_steps(PUEBLO_DOMESTIC_HOURLY)
    irr_steps = _hourly_to_steps(IRRIGATION_HOURLY)

    # Pérdidas de fondo de red (fugas difusas "legítimas" ya presentes): 5-12%
    background_loss_frac = rng.uniform(0.05, 0.12)

    daily_liters = np.zeros((days, STEPS_PER_DAY))
    for d in range(days):
        weekday = (start + timedelta(days=d)).weekday()
        weekend_boost = 1.08 if weekday >= 5 else 1.0
        vol = homes * liters_per_home_day * weekend_boost
        day_curve = vol * dom_steps
        # Riego doméstico/municipal en temporada
        if temps[d] > 20:
            irr_vol = homes * rng.uniform(15, 45) * min(1.0, (temps[d] - 20) / 8)
            day_curve = day_curve + irr_vol * irr_steps

        rel_sigma = 0.35 / np.sqrt(homes / 10)  # suavizado por agregación
        noise = rng.normal(1.0, rel_sigma, STEPS_PER_DAY)
        daily_liters[d] = np.maximum(0, day_curve * noise)

    liters = daily_liters.ravel()
    flow_lpm = liters / RESOLUTION_MIN
    # Pérdida de fondo constante (el suelo nocturno legítimo de una red real)
    flow_lpm = flow_lpm + background_loss_frac * flow_lpm.mean()
    mean_flow = float(flow_lpm.mean())
    flow_lpm, is_leak = _inject_leaks(flow_lpm, mean_flow, rng)

    covars = pd.DataFrame({
        "household_id": meter_id,
        "date": [(start + timedelta(days=d)).strftime("%Y-%m-%d") for d in range(days)],
        "occupancy": np.nan,
        "temp_c": np.round(temps, 1),
        "meter_type": "pueblo",
        "units": homes,
    })
    return flow_lpm * RESOLUTION_MIN, is_leak, covars


# ----------------------------------------------------------------------
def main():
    cfg = AGG_CONFIG
    rng = np.random.default_rng(cfg["seed"])
    random.seed(cfg["seed"])
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    days = cfg["simulation_days"]
    index = pd.date_range(start=start, periods=days * STEPS_PER_DAY,
                          freq=f"{RESOLUTION_MIN}min")

    frames, covar_frames = [], []

    print(f"Simulando {cfg['n_hotels']} hoteles y {cfg['n_pueblos']} pueblos/DMA · {days} días\n")

    for i in range(cfg["n_hotels"]):
        rooms_seed = rng.integers(1000, 9999)
        meter_id = f"meter_hotel_{rooms_seed}"
        liters, is_leak, covars = simulate_hotel(meter_id, days, start, rng)
        frames.append(pd.DataFrame({
            "timestamp": index, "consumption_l": np.round(liters, 2),
            "is_leak": is_leak, "household_id": meter_id,
        }))
        covar_frames.append(covars)
        print(f"  🏨 {meter_id}: {covars['units'].iloc[0]} hab · "
              f"{liters.sum()/days/1000:.1f} m³/día · fuga: {'sí' if is_leak.any() else 'no'}")

    for i in range(cfg["n_pueblos"]):
        seed_id = rng.integers(1000, 9999)
        meter_id = f"meter_pueblo_{seed_id}"
        liters, is_leak, covars = simulate_pueblo(meter_id, days, start, rng)
        frames.append(pd.DataFrame({
            "timestamp": index, "consumption_l": np.round(liters, 2),
            "is_leak": is_leak, "household_id": meter_id,
        }))
        covar_frames.append(covars)
        print(f"  🏘️  {meter_id}: {covars['units'].iloc[0]} viviendas · "
              f"{liters.sum()/days/1000:.1f} m³/día · fuga: {'sí' if is_leak.any() else 'no'}")

    dataset = pd.concat(frames, ignore_index=True)
    covariates = pd.concat(covar_frames, ignore_index=True)

    os.makedirs("data", exist_ok=True)
    out_data = "data/aggregated_meters_dataset.csv"
    out_cov = "data/aggregated_meters_covariates.csv"
    dataset.to_csv(out_data, index=False)
    covariates.to_csv(out_cov, index=False)

    leak_rows = int(dataset["is_leak"].sum())
    meters_with_leak = dataset.loc[dataset["is_leak"] == 1, "household_id"].nunique()
    print(f"\n📊 Dataset: {len(dataset):,} filas · {dataset['household_id'].nunique()} contadores")
    print(f"   Fugas: {meters_with_leak} contadores afectados · "
          f"{leak_rows:,} intervalos ({leak_rows/len(dataset)*100:.2f}%)")
    print(f"💾 {out_data}\n💾 {out_cov}")


if __name__ == "__main__":
    main()
