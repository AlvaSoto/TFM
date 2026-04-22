import numpy as np #ignore
import pandas as pd
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

class Settings:
    # /Users/sotoa/Documents/TFM/Repository/TFM
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    DATA_DIR = BASE_DIR / "data" / "mixed_population_dataset_160_households_more_leaks.csv"
    MODELS_DIR = BASE_DIR / "app" / "simulators" / "Azure_model_new_data/resultados/Run_Ultimate/checkpoints/best_model.keras"
    SCALER_PATH = BASE_DIR / "app" / "simulators" / "Azure_model_new_data/resultados/Run_Ultimate/results/scaler.joblib"

    LEAK_THRESHOLD: float = 0.5213  # Threshold for classifying a sequence as leak or no leak

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")


settings = Settings()

"""
Global parameters for the simulation

This values control the behavour of each individual simulation
"""

SIMULATION_CONFIG = {
    "simulation_days": 180,#Number of days to simulate for each household. Main() use it for simulate_events() & inject_leak()
    "time_resolution_minutes": 15,#Every 15 mins we get the consumption, so 60 mins/15=4 intervals, 4 x 24h=96
    "leak_probability": 0.7, #70% of households will have at least one leak - increased to improve class balance
    "leak_flow_rate_mean": 1.2, #Mean flow rate for leaks (L/min) - realistic for small-to-medium leaks
    "leak_flow_rate_std": 0.3, #Standard deviation for leak flow rate variability
    "leak_duration_hours_mean": 48, #Mean duration of leaks (hours) - 2 days average
    "leak_duration_hours_std": 24, #Standard deviation for leak duration (hours) - allows 24h to 72h range
    "leak_min_duration_hours": 24, #Minimum leak duration (hours) - ensures leaks are detectable
    "leak_max_duration_hours": 120, #Maximum leak duration (hours) - up to 5 days
    "leaks_per_household_mean": 1.5, #Mean number of leaks per household (Poisson distribution) - allows multiple leaks
    "leak_min_gap_hours": 72, #Minimum gap between leaks in the same household (hours) - prevents overlapping leaks
    "leak_intermittent_probability": 0.2, #20% of leaks are intermittent (on/off cycles)
    "leak_intermittent_cycle_hours": 12, #For intermittent leaks: cycle duration (hours on, hours off)
}

#Probability that an event will occur each hour of the day
"""
Numpy Arrays of 24 alues that sums 1.0. Used by generate event times()

3 types:
- Personal Hygiene: HOURLY_PROBABILITY_COMMON. Peaks morning (7-9h) night (19-22h)
- Meals: HOURLY_PROBABILITY_MEALS. Peaks (7-9h) (13-15h) (20-22h)
- Pattern for electrical appliances: 


"""
HOURLY_PROBABILITY_COMMON = np.array([
    0.01, 0.01, 0.01, 0.01, 0.2, 0.04, 0.08, 0.10, 0.008, 0.04, #00h-09h
    0.03, 0.03, 0.04, 0.04, 0.03, 0.03, 0.04, 0.05, 0.06, 0.08, #10h-19h
    0.10, 0.08, 0.05, 0.02                                      #20h-23h
])

"""
Then normalise to compare values with different units or create distributions to 
represent %, compare days, hours

X_normalised = xi/sum(x)
"""

HOURLY_PROBABILITY_COMMON /= HOURLY_PROBABILITY_COMMON.sum()

HOURLY_PROBABILITY_MEALS = np.array([
    0.01, 0.01, 0.01, 0.01, 0.02, 0.05, 0.10, 0.12, 0.10, 0.05,  # 00h-09h (Breakfast peak)
    0.02, 0.02, 0.08, 0.12, 0.10, 0.05, 0.02, 0.02, 0.02, 0.03,  # 10h-19h (Lunch Peak)
    0.08, 0.10, 0.08, 0.01                                    # 20h-23h (Dinner Peak)
])
HOURLY_PROBABILITY_MEALS /= HOURLY_PROBABILITY_MEALS.sum()


HOURLY_PROBABILITY_APPLIANCE = np.array([
    0.06, 0.05, 0.04, 0.03, 0.02, 0.02, 0.03, 0.04, 0.04, 0.03,
    0.03, 0.03, 0.03, 0.04, 0.04, 0.04, 0.04, 0.04, 0.05, 0.05,
    0.06, 0.07, 0.07, 0.06
])
HOURLY_PROBABILITY_APPLIANCE /= HOURLY_PROBABILITY_APPLIANCE.sum()

#Definition of the event types

EVENT_CATALOG = {
    "shower": {
        "frequency_per_day": 1.0, 
        "duration_mean": 8.0,
        "duration_std": 3.0,
        "flow_rate_mean": 7.0, #L/min
        "flow_rate_std": 1.5,
        "hourly_probability": HOURLY_PROBABILITY_COMMON
    },
    "toilet_flush": {
        "frequency_per_day": 4.0, 
        "duration_mean": 0.5,
        "duration_std": 0.1,
        "flow_rate_mean": 6.0,
        "flow_rate_std": 1.0,
        "hourly_probability": HOURLY_PROBABILITY_COMMON
    },
    "tap_use_bathroom": {
        "frequency_per_day": 6.0, 
        "duration_mean": 0.5,
        "duration_std": 0.4,
        "flow_rate_mean": 4.0,
        "flow_rate_std": 1.0,
        "hourly_probability": HOURLY_PROBABILITY_COMMON
    },
    "tap_use_kitchen": {
        "frequency_per_day": 5.0,
        "duration_mean": 1.0,
        "duration_std": 0.8,
        "flow_rate_mean": 5.0,
        "flow_rate_std": 1.0,
        "hourly_probability": HOURLY_PROBABILITY_MEALS
    },
    "dishwasher": {
        "frequency_per_day": 0.5, #One day on one day off
        "duration_mean": 60.0,
        "duration_std": 10.0,
        "flow_rate_mean": 0.2,
        "flow_rate_std": 0.05,
        "hourly_probability": HOURLY_PROBABILITY_APPLIANCE
    },
    "washing_machine": {
        "frequency_per_day": 0.3, #Occurs every 3 days
        "duration_mean": 50.0, #50 mins average cycle duration (~50L per cycle at 1.0 L/min)
        "duration_std": 10.0, #standard deviation
        "flow_rate_mean": 1.0, #1.0 L/min - realistic flow rate for modern washing machines during active cycles (filling, rinsing). ~50L per cycle.
        "flow_rate_std": 0.15, #Standard deviation to reflect variability in cycle stages
        "hourly_probability": HOURLY_PROBABILITY_APPLIANCE
    },
    "gardening": {
        "frequency_per_day": 0.15,
        "duration_mean": 15.0,
        "duration_std": 5.0,
        "flow_rate_mean": 10.0,
        "flow_rate_std": 2.0,
        "hourly_probability": HOURLY_PROBABILITY_APPLIANCE
    }
}

#Household profiles
DEFAULT_HOUSEHOLD_PROFILES = {
    "apartment_single_person": {
        "name": "apartment_single_person",
        "num_people": 1,
        "events": {
            "shower": EVENT_CATALOG["shower"],
            "toilet_flush": EVENT_CATALOG["toilet_flush"],
            "tap_use_bathroom": EVENT_CATALOG["tap_use_bathroom"],
            "tap_use_kitchen": EVENT_CATALOG["tap_use_kitchen"],
            "dishwasher": EVENT_CATALOG["dishwasher"],
            "washing_machine": EVENT_CATALOG["washing_machine"]
        }
    },

    "aparment_family": {
        "name": "apartment_family",
        "num_people": 4,
        "events": {
            "shower": EVENT_CATALOG["shower"],
            "toilet_flush": EVENT_CATALOG["toilet_flush"],
            "tap_use_bathroom": EVENT_CATALOG["tap_use_bathroom"],
            "tap_use_kitchen": EVENT_CATALOG["tap_use_kitchen"],
            "dishwasher": {**EVENT_CATALOG["dishwasher"], "frequency_per_day":1.0},
            "washing_machine": {**EVENT_CATALOG["washing_machine"], "frequency_per_day": 0.8}
        }
    },
    "house_family_garden": {
        "name": "house_family_garden",
        "num_people": 4,
        "events": {
            "shower": EVENT_CATALOG["shower"],
            "toilet_flush": EVENT_CATALOG["toilet_flush"],
            "tap_use_bathroom": EVENT_CATALOG["tap_use_bathroom"],
            "tap_use_kitchen": EVENT_CATALOG["tap_use_kitchen"],
            "dishwasher": {**EVENT_CATALOG["dishwasher"], "frequency_per_day": 1.0},
            "washing_machine": {**EVENT_CATALOG["washing_machine"], "frequency_per_day": 0.8},
            "gardening": EVENT_CATALOG["gardening"]
        }
    }
}

#This is for phase 2 EStacionalidad

SEASONAL_MULTIPLAYERS = {
    #Month: (Multiplier showers, Multipliers Gardening, Multiplier for washing_machine)
    1: (0.9, 0.0, 0.9),
    2: (0.9, 0.0, 0.9),
    3: (1.0, 0.1, 1.0),
    4: (1.0, 0.3, 1.0),
    5: (1.1, 0.8, 1.1),
    6: (1.2, 1.0, 1.2),
    7: (1.3, 1.0, 1.2),
    8: (1.2, 0.9, 1.2),
    9: (1.1, 0.5, 1.1),
    10: (1.0, 0.2, 1.0),
    11: (1.0, 0.0, 1.0),
    12: (0.9, 0.0, 1.0)
}
