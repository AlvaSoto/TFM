import numpy as np
import pandas as pd
from typing import List, Tuple, Optional
import random
from dataclasses import dataclass, field
import os 
from datetime import datetime, timedelta
from app.models.water_classes import WaterEvent, LeakEvent
from app.core.simulation_config import SIMULATION_CONFIG, DEFAULT_HOUSEHOLD_PROFILES, EVENT_CATALOG

#Template to create objects

class WaterConsumptionSimulator:

    def __init__(self, household_profile: dict, random_seed: Optional[int] = None):
        self.household_profile = household_profile
        self.household_id = f"household_{household_profile['name']}_{random.randint(1000,9999)}"
        self.start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        if random_seed:
            np.random.seed(random_seed)
            random.seed(random_seed)

        print(f"🚰 Starting simulation for the house {household_profile['name']}")
        print(f"👥 People: {household_profile['num_people']}")
        print(f"🏠 Household ID: {self.household_id}")


    """
    This is the WHEN. Defines the exact moment when the event occurs and what tipe of event
    """
    def _generate_event_times(self, event_config: dict, simulation_days: int) -> List[datetime]:
        """
        It generates the event times bases on the Poisson Process
        event_config: i send the config for the specific event(shower for example)
        simulation_days: 
        """

        #1. Calculate how many events will occur in total
        """
        I cant multiply the frequency x the days because it will provide a deterministic result
        (1 shower/day * 3days= 3 showers in total). The reality is stochastic.

        Then How to do it?

        Poisson Distribution is ideal too. It models the number of times that an event occurs in 
        a fixed interval of time, if the events occurs randomly and independently, but 
        with a constant average rate

        """
        event_times = []

        total_frequency = event_config['frequency_per_day'] * self.household_profile['num_people'] * simulation_days
        num_events = np.random.poisson(total_frequency)

        #Asign a timestamp for each event
        for _ in range(num_events): #_ indicates that it does not matter the i (the loop counter)
            day = random.randint(0, simulation_days -1) #I choose a random value within the simulation range
            hour = np.random.choice(24, p=event_config['hourly_probability'])
            minute = random.randint(0,59)
            second = random.randint(0,59)

            event_time = self.start_date + timedelta(days=day, hours=hour, minutes=minute, seconds=second)
            event_times.append(event_time)

        #returning sorted event times
        return sorted(event_times)
    
    def _generate_event_characteristics(self, event_config: dict) -> Tuple[float, float]:
        """
        It generates the duration and the water flow per liter for a new event but randomly
        """
        # Duratio generation using a Normal distribution
        duration = max(0.1, np.random.normal(event_config['duration_mean'], event_config['duration_std']))

        # Flow rate generation using a Normal distribution
        flow_rate = max(0.1, np.random.normal(event_config['flow_rate_mean'], event_config['flow_rate_std']))

        return duration, flow_rate
    

    #


    def simulate_events(self, simulation_days: int) -> List[WaterEvent]:
        """
        Simulate all the consumption events for the specific period.

        This function orchestrates the 2 specialists (_generate_event_characteristics, _generate_event_times)
        to build a complet list with all the consumption events that occurs during the simulation
        """

        all_events = []
        print(f"📊 Simulating events for {simulation_days} day(s)...")

        #Loop that runs the event types defined in the configuration (shower, toilet_flush..)
        for event_type, event_config in self.household_profile['events'].items():
            #1 call each individual event
            event_times = self._generate_event_times(event_config, simulation_days)

            for time in event_times:
                duration, flow_rate = self._generate_event_characteristics(event_config)

                #Creation of the WaterEvent final object
                all_events.append(WaterEvent(
                    event_type=event_type,
                    start_time=time,
                    duration_minutes=duration,
                    flow_rate_lpm=flow_rate,
                    household_id=self.household_id
                ))

        print(f"✅ {len(all_events)} generated events")
        return all_events
    
    def inject_leak(self, simulation_days: int) -> Optional[LeakEvent]:
        """
        This function defines if there should be a leak or not. If so, create the object

        This object will be the ground of truth 
        """

        # Is there any leak?
        # random.random returns a value between 0-1
        """
        Imagine SIMULATION_CONFIG["leak_probability"] = 0.2 (20% leaks, 80% no leaks)
        If random > 0.2 no leak
        """

        if random.random() > SIMULATION_CONFIG["leak_probability"]:
            return None
        
        total_simulation_hours = simulation_days * 24
        leak_duration_hours = SIMULATION_CONFIG["leak_duration_hours"]

        # Creating an starting secure point 
        start_hour_offset = random.randint(0, total_simulation_hours - leak_duration_hours)
        start_time = self.start_date + timedelta(hours=start_hour_offset)
        end_time = start_time + timedelta(hours=leak_duration_hours)

        #Creating the leak object
        leak = LeakEvent(
            start_time = start_time,
            end_time = end_time,
            flow_rate_lpm = SIMULATION_CONFIG["leak_flow_rate"],
            household_id = self.household_id
        )

        print(f"Leak active from {start_time} to {end_time}")
        return leak
    

    def aggregate_to_time_series(self, events: List[WaterEvent], leak: Optional[LeakEvent], simulation_days:int) -> pd.DataFrame:
        """
        Convert the continuous events into discret events 
        """
        #Create the timeline 
        resolution = timedelta(minutes=SIMULATION_CONFIG["time_resolution_minutes"])
        end_time = self.start_date + timedelta(days=simulation_days)
        time_index = pd.date_range(start=self.start_date, end=end_time, freq=resolution, inclusive='left')
        df = pd.DataFrame(0.0, index=time_index, columns=['consumption_l', 'is_leak'])


        #Process and draw the events in the timeline
        for event in events:
            event_end_time = event.start_time + timedelta(minutes=event.duration_minutes)
            current_time = event.start_time
            while current_time < event_end_time:
                #finde the slot of time which this current event belongs
                time_slot = current_time.replace(
                    minute=(current_time.minute // SIMULATION_CONFIG['time_resolution_minutes']) * SIMULATION_CONFIG['time_resolution_minutes'],
                    second=0, microsecond=0)
                
                if time_slot in df.index:
                    # calculate number of minutes that are in the slot 
                    next_slot = time_slot + resolution
                    overlap_end = min(event_end_time, next_slot)
                    overlap_duration = (overlap_end - current_time).total_seconds() / 60
                    
                    df.loc[time_slot, 'consumption_l'] += overlap_duration * event.flow_rate_lpm
                    current_time = next_slot
                else:
                    # In case the event overextends
                    break

        # Process the leak 
        if leak:
            leak_mask = (df.index >= leak.start_time) & (df.index < leak.end_time)
            df.loc[leak_mask, 'consumption_l'] += SIMULATION_CONFIG['time_resolution_minutes'] * leak.flow_rate_lpm
            df.loc[leak_mask, 'is_leak'] = 1
        
        df['is_leak'] = df['is_leak'].astype(int)
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'timestamp'}, inplace=True)
        df['household_id'] = self.household_id
        
        print(f"   ✅ Temporal series generated {len(df)} points.")
        return df


def main():
    """
    To run the simulation 
    """

    print("🚰 Smart Water Assistant - Raw Data Simulator")
    print("=" * 50)

    #Step 1: To set the simulation
    NUM_HOUSEHOLDS_TO_SIMULATE = 160
    available_household_profile = list(DEFAULT_HOUSEHOLD_PROFILES.values())
    all_households_df = []
    #List to save the events
    all_events_list = []

    print(f"Starting the simulation for {NUM_HOUSEHOLDS_TO_SIMULATE} households of all tipes ")

    for i in range(NUM_HOUSEHOLDS_TO_SIMULATE):

        #Choose a random profile per household
        random_profile = random.choice(available_household_profile)

        print(f"\n--- Simulating household {i+1}/{NUM_HOUSEHOLDS_TO_SIMULATE} (Tipo: {random_profile['name']})---")

        simulator = WaterConsumptionSimulator(random_profile, random_seed=i)

        #Step 2: Simulate consumption events and possible leaks
        events = simulator.simulate_events(simulation_days=SIMULATION_CONFIG["simulation_days"])
        leak = simulator.inject_leak(simulation_days=SIMULATION_CONFIG["simulation_days"])

        #Step 3: Add the data to a temporary series
        consumption_df = simulator.aggregate_to_time_series(events, leak, simulation_days=SIMULATION_CONFIG["simulation_days"])

        all_households_df.append(consumption_df)
        all_events_list.extend(events)

    print("\n Simulation completed for all the households✅")
    final_dataset = pd.concat(all_households_df, ignore_index=True)
    
    # --- CALCULATE AND DISPLAY GLOBAL STATISTICS FOR THE FINAL DATASET ---
    print("\n📊 Final Dataset Statistics (Mixed Population):")
    
    # General stats
    total_households = final_dataset['household_id'].nunique()
    print(f"   🏠 Total unique households simulated: {total_households}")
    print(f"   📈 Total data points (rows): {len(final_dataset):,}")
    
    # Profile distribution stats
    print(f"   🏘️ Distribution of simulated household types:")
    # This code extracts the profile name from the household_id to count how many of each type were simulated.
    profile_counts = final_dataset['household_id'].str.split('_').str[1].value_counts()
    print(profile_counts.to_string())

    # Total consumption stats
    total_consumption = final_dataset['consumption_l'].sum()
    print(f"   💧 Total consumption across all households: {total_consumption:,.2f} L")
    
    # --- LEAK STATISTICS CALCULATION ---
    # Count how many unique households had a leak injected.
    households_with_leaks = final_dataset[final_dataset['is_leak'] == 1]['household_id'].nunique()
    
    if households_with_leaks > 0:
        print(f"\n   --- Leak Statistics ---")
        print(f"   🚨 Leaks were injected in {households_with_leaks} out of {total_households} households ({households_with_leaks/total_households:.1%}).")

        # Calculate the total consumption attributable ONLY to leaks.
        # For each row where 'is_leak' is 1, the leak consumption is constant.
        leak_consumption_per_period = SIMULATION_CONFIG['time_resolution_minutes'] * SIMULATION_CONFIG['leak_flow_rate']
        
        # Count the total number of 15-minute periods that have a leak.
        # Since 'is_leak' is 0 or 1, sum() is a fast way to count the 1s.
        total_leak_periods = final_dataset['is_leak'].sum()
        
        # The total consumption from leaks is the number of periods times the consumption in each one.
        total_leak_consumption = total_leak_periods * leak_consumption_per_period
        
        print(f"   💧 Total consumption from leaks only: {total_leak_consumption:,.2f} L")
        print(f"   💧 Percentage of total consumption due to leaks: {total_leak_consumption / total_consumption:.1%}")

    else:
        print("\n   🚨 No leaks were injected in this simulation batch.")

    # --- SAVE THE FINAL, COMPLETE DATASET ---
    output_dir = 'data'
    # os.makedirs creates the directory if it doesn't already exist.
    # exist_ok=True prevents an error if the directory is already there.
    os.makedirs(output_dir, exist_ok=True)
    
    # os.path.join creates a file path that is compatible with any OS (Windows, Mac, Linux).
    output_path = os.path.join(output_dir, f"mixed_population_dataset_{NUM_HOUSEHOLDS_TO_SIMULATE}_households.csv")
    
    # Export the DataFrame to a CSV file.
    # index=False prevents pandas from writing the DataFrame index as a column in the CSV.
    final_dataset.to_csv(output_path, index=False)
    
    print(f"\n💾 Full mixed dataset saved to: {output_path}")

    print("\nConsolidating the detailed events log...")

    event_data = [
        {
            "household_id": e.household_id,
            "event_type": e.event_type,
            "start_time": e.start_time,
            "duration_minutes": round(e.duration_minutes, 2),
            "flow_rate_lpm": round(e.flow_rate_lpm, 2),
            "total_consumption_l": round(e.total_consumption_l)
        }
        for e in all_events_list
    ]

    events_df = pd.DataFrame(event_data)

    output_path_events = os.path.join(output_dir, f"detailed_events_log_{NUM_HOUSEHOLDS_TO_SIMULATE}_households.csv")

    events_df.to_csv(output_path_events, index=False)
    print(f"Detailed events log saved in {output_path_events}")

if __name__ == "__main__":
    main()




