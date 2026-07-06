"""
Regla de Caudal Mínimo Nocturno (MNF, Minimum Night Flow).

Es el método clásico de la industria (ver memoria, sección 2.3.1): durante la
madrugada el consumo legítimo de un hogar debería tocar cero en algún momento.
Si el caudal NUNCA baja de un suelo durante toda la ventana nocturna, hay agua
circulando de forma continua: la firma física de una fuga.

Se usa como CONFIRMADOR del modelo ML en el ensemble de la vista de flota:
  - ML + MNF de acuerdo  -> alerta CONFIRMADA (alta precisión)
  - solo uno de los dos  -> SOSPECHA (revisar)

Es intencionadamente simple, explicable ante una gestora ("el contador no ha
parado en toda la noche") y ejecutable en el propio contador (edge).
"""
import pandas as pd

# Ventana nocturna: 01:00-05:59 (se evita medianoche, aún con actividad humana)
NIGHT_START_HOUR = 1
NIGHT_END_HOUR = 5

# Suelo nocturno: si TODOS los intervalos de 15 min de la noche superan estos
# litros, el agua no ha dejado de correr. 2 L/15min = 0.13 L/min, muy por
# debajo de cualquier fuga relevante (0.3+ L/min) y por encima del ruido.
FLOOR_LITERS_PER_INTERVAL = 2.0

# Persistencia: nº mínimo de noches con suelo para considerar alerta MNF
MIN_NIGHTS = 2


def mnf_analysis(df: pd.DataFrame) -> dict:
    """
    Analiza el caudal mínimo nocturno de un hogar.

    df: lecturas crudas con columnas timestamp (datetime) y consumption_l.
    Devuelve las noches cuyo caudal nunca bajó del suelo y si constituyen alerta.
    """
    ts = pd.to_datetime(df["timestamp"])
    night_mask = ts.dt.hour.between(NIGHT_START_HOUR, NIGHT_END_HOUR)
    night = df.loc[night_mask].copy()
    if night.empty:
        return {"mnf_alert": False, "mnf_days": [], "max_night_floor_l": 0.0, "nights_analyzed": 0}

    night_dates = ts.loc[night_mask].dt.strftime("%Y-%m-%d")
    # Suelo de cada noche = mínimo de los intervalos de 15 min de esa madrugada
    floors = night.groupby(night_dates.values)["consumption_l"].min()

    mnf_days = sorted(floors[floors > FLOOR_LITERS_PER_INTERVAL].index.tolist())

    return {
        "mnf_alert": len(mnf_days) >= MIN_NIGHTS,
        "mnf_days": mnf_days,
        "max_night_floor_l": round(float(floors.max()), 1),
        "nights_analyzed": int(len(floors)),
    }


def mnf_trending(df: pd.DataFrame, baseline_nights: int = 28, rel_delta: float = 0.15,
                 abs_delta_l: float = 2.0, min_nights: int = 2) -> dict:
    """
    MNF-TRENDING: la versión del caudal mínimo nocturno para contadores
    AGREGADOS (hoteles, pueblos/DMA), donde el suelo nocturno legítimo nunca
    es cero (lavandería, riego, pérdidas de fondo) y la regla absoluta no vale.

    Compara el mínimo nocturno de cada noche contra la MEDIANA MÓVIL de las
    `baseline_nights` noches anteriores (mediana = robusta a noches con fuga).
    Alerta si el suelo supera baseline*(1+rel_delta) + abs_delta_l durante
    `min_nights` noches consecutivas.

    En un hogar la línea base es ~0, así que degenera en la regla absoluta:
    un único algoritmo para todos los segmentos.
    """
    ts = pd.to_datetime(df["timestamp"])
    night_mask = ts.dt.hour.between(NIGHT_START_HOUR, NIGHT_END_HOUR)
    night = df.loc[night_mask]
    if night.empty:
        return {"mnf_alert": False, "mnf_days": [], "max_night_floor_l": 0.0, "nights_analyzed": 0}

    night_dates = ts.loc[night_mask].dt.strftime("%Y-%m-%d")
    floors = night.groupby(night_dates.values)["consumption_l"].min().sort_index()

    baseline = floors.rolling(baseline_nights, min_periods=7).median().shift(1)
    threshold = baseline * (1 + rel_delta) + abs_delta_l
    exceeds = (floors > threshold) & baseline.notna()

    # Persistencia: noches que forman parte de una racha >= min_nights
    flagged = []
    run = []
    for day, hit in exceeds.items():
        if hit:
            run.append(day)
        else:
            if len(run) >= min_nights:
                flagged.extend(run)
            run = []
    if len(run) >= min_nights:
        flagged.extend(run)

    return {
        "mnf_alert": len(flagged) >= min_nights,
        "mnf_days": sorted(flagged),
        "max_night_floor_l": round(float(floors.max()), 1),
        "nights_analyzed": int(len(floors)),
    }


def combine_alert_level(ml_alert: bool, mnf_alert: bool) -> str:
    """
    Nivel de alerta del ensemble para la cola de intervención.

    Lógica basada en la evaluación 2026-07-06 sobre hogares nunca vistos:
    el MNF solo alcanzó P=1.0 / R=0.815 a nivel hogar, mientras que exigir
    confirmación del ML (AND) bajaba el recall a 0.667 sin ganar precisión.
    Por eso: la regla física confirma por sí sola; el ML amplía cobertura.

    Caveat mundo real: con datos reales el MNF tendrá falsos suelos (riego
    nocturno programado, descalcificadores) que el simulador no modela —
    recalibrar este reparto de pesos durante el piloto.
    """
    if mnf_alert:
        return "CONFIRMADA"  # caudal nocturno continuo: firma física de fuga
    if ml_alert:
        return "SOSPECHA"    # el modelo IA ve un patrón anómalo sin confirmación física
    return "OK"
