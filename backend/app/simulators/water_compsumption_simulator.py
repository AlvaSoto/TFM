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
            # Imagine a roulette with 24 slots (hours) with different probabilities, the slot of 8am is more probable than 3am
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

        It returns a tuple with (duration, flow_rate)
        1. Duration in minutes
        2. Flow rate in L/min
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
    
    def inject_leak(self, simulation_days: int) -> List[LeakEvent]:
        """
        This function defines if there should be leaks or not. If so, creates leak objects.
        Now supports multiple leaks per household with variability in flow rate and duration.
        
        Returns a list of LeakEvent objects (can be empty if no leaks)
        """

        """
        1. Decide if a household will have leaks or not
        """

        # Decide if this household will have leaks
        # it is set to a leak_probability of 0.7, which means 70% of households will have leaks
        # it follows a Bernoulli distribution (yes/no)
        # if the number is higher than 0.7, no leaks for this household
        if random.random() > SIMULATION_CONFIG["leak_probability"]:
            return []
        
        total_simulation_hours = simulation_days * 24
        leaks = []

        """
        2. Then if a household will have leaks,determine how many leaks and how serious they are
        """
        
        # Determine number of leaks for this household (Poisson distribution)
        # it is set to an average of 1.5 leaks per household following a Poisson distribution
        # that means that some households will have 1 leak, some 2, some 3, etc. in 6 months
        num_leaks = np.random.poisson(SIMULATION_CONFIG["leaks_per_household_mean"])
        # Ensure at least one leak
        num_leaks = max(1, num_leaks)  # At least 1 leak if household is selected
        
        # Track used time slots to prevent overlapping leaks
        used_slots = []
        
        for leak_idx in range(num_leaks):
            # Generate leak characteristics with variability
            leak_flow_rate = max(0.3, np.random.normal(
                SIMULATION_CONFIG["leak_flow_rate_mean"],
                SIMULATION_CONFIG["leak_flow_rate_std"]
            ))
            
            """
            3. Here we use the clamping o recorte

            Why? 
            
            - Because the normal distribution could say a leak last 500h, but i have limited it to 120h max
            - Because the normal distribution could say a leak last 10h, but i have limited it to 24h min
            """
            leak_duration_hours = max(
                SIMULATION_CONFIG["leak_min_duration_hours"],
                min(
                    SIMULATION_CONFIG["leak_max_duration_hours"],
                    np.random.normal(
                        SIMULATION_CONFIG["leak_duration_hours_mean"],
                        SIMULATION_CONFIG["leak_duration_hours_std"]
                    )
                )
            )
            
            # Find a valid time slot that doesn't overlap with previous leaks
            max_attempts = 50
            attempt = 0
            valid_slot = False
        
            """
            4. Imagine thay i have to place 2 leaks in a calendar of 180 days, but the 2 leaks cannot overlap.
            Then i have to check that the new leak does not overlap with the previous one. If it does, i have to try again
            until i find a valid slot or reach the maximum number of attempts: 50
            """
            
            while attempt < max_attempts and not valid_slot:
                start_hour_offset = random.randint(0, max(1, total_simulation_hours - int(leak_duration_hours)))
                start_time = self.start_date + timedelta(hours=start_hour_offset)
                end_time = start_time + timedelta(hours=leak_duration_hours)
                
                # Check if this slot overlaps with previous leaks
                overlaps = False
                for prev_start, prev_end in used_slots:
                    if not (end_time <= prev_start or start_time >= prev_end):
                        overlaps = True
                        break
                
                if not overlaps:
                    valid_slot = True
                    used_slots.append((start_time, end_time))
                else:
                    attempt += 1
            
            if not valid_slot:
                continue  # Skip this leak if we can't find a valid slot
        
            """
            5. Now the code decides if the leak is intermittent (cistern that leaks water only intermittently / 12h on, 12h off) 
            or continuous (a broken pipe that leaks water all the time)
            """
            
            # Check if this leak should be intermittent
            is_intermittent = random.random() < SIMULATION_CONFIG["leak_intermittent_probability"]
            
            if is_intermittent:
                # For intermittent leaks, create multiple leak events with on/off cycles
                cycle_hours = SIMULATION_CONFIG["leak_intermittent_cycle_hours"]
                current_time = start_time
                cycle_on = True
                
                while current_time < end_time:
                    if cycle_on:
                        cycle_end = min(current_time + timedelta(hours=cycle_hours), end_time)
                        leak = LeakEvent(
                            start_time=current_time,
                            end_time=cycle_end,
                            flow_rate_lpm=leak_flow_rate,
                            household_id=self.household_id
                        )
                        leaks.append(leak)
                        current_time = cycle_end
                    else:
                        # Off cycle - skip this period
                        current_time = min(current_time + timedelta(hours=cycle_hours), end_time)
                    cycle_on = not cycle_on
            else:
                # Continuous leak
                leak = LeakEvent(
                    start_time=start_time,
                    end_time=end_time,
                    flow_rate_lpm=leak_flow_rate,
                    household_id=self.household_id
                )
                leaks.append(leak)
        
        if leaks:
            print(f"Generated {len(leaks)} leak(s) for household {self.household_id}")
            for leak in leaks:
                print(f"  - Leak: {leak.start_time} to {leak.end_time}, flow: {leak.flow_rate_lpm:.2f} L/min")
        
        return leaks
    

    def aggregate_to_time_series(self, events: List[WaterEvent], leaks: List[LeakEvent], simulation_days:int) -> pd.DataFrame:
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

        # Process all leaks
        if leaks:
            for leak in leaks:
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
    #List to save the leaks
    all_leaks_list = []

    print(f"Starting the simulation for {NUM_HOUSEHOLDS_TO_SIMULATE} households of all tipes ")

    for i in range(NUM_HOUSEHOLDS_TO_SIMULATE):

        #Choose a random profile per household
        random_profile = random.choice(available_household_profile)

        print(f"\n--- Simulating household {i+1}/{NUM_HOUSEHOLDS_TO_SIMULATE} (Tipo: {random_profile['name']})---")

        simulator = WaterConsumptionSimulator(random_profile, random_seed=i)

        #Step 2: Simulate consumption events and possible leaks
        events = simulator.simulate_events(simulation_days=SIMULATION_CONFIG["simulation_days"])
        leaks = simulator.inject_leak(simulation_days=SIMULATION_CONFIG["simulation_days"])

        #Step 3: Add the data to a temporary series
        consumption_df = simulator.aggregate_to_time_series(events, leaks, simulation_days=SIMULATION_CONFIG["simulation_days"])

        all_households_df.append(consumption_df)
        all_events_list.extend(events)
        all_leaks_list.extend(leaks)

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
    
    # --- LEAK STATISTICS CALCULATION (CORREGIDO) ---
    # Count how many unique households had a leak injected.
    households_with_leaks = final_dataset[final_dataset['is_leak'] == 1]['household_id'].nunique()
    
    if households_with_leaks > 0:
        print(f"\n   --- Leak Statistics ---")
        print(f"   🚨 Leaks were injected in {households_with_leaks} out of {total_households} households ({households_with_leaks/total_households:.1%}).")

        # CÁLCULO CORREGIDO:
        # Como ahora el caudal de fuga es variable, calculamos el consumo total de fugas
        # sumando el consumo real de cada objeto LeakEvent generado.
        total_leak_consumption = sum(l.total_consumption_l for l in all_leaks_list)
        
        # Calculate percentage of data points with leaks (CRITICAL for model training)
        total_leak_periods = final_dataset['is_leak'].sum()
        leak_data_percentage = (total_leak_periods / len(final_dataset)) * 100
        
        print(f"   💧 Total consumption from leaks only: {total_leak_consumption:,.2f} L")
        print(f"   💧 Percentage of total consumption due to leaks: {total_leak_consumption / total_consumption:.1%}")
        print(f"   📊 Total number of leak events: {len(all_leaks_list)}")
        print(f"   📈 Data points with leaks: {total_leak_periods:,} out of {len(final_dataset):,} ({leak_data_percentage:.2f}%)")
        print(f"   ⚖️  Class balance ratio (Normal:Leak): {(len(final_dataset) - total_leak_periods) / total_leak_periods:.1f}:1")

    else:
        print("\n   🚨 No leaks were injected in this simulation batch.")

    # --- SAVE THE FINAL, COMPLETE DATASET ---
    output_dir = 'data'
    # os.makedirs creates the directory if it doesn't already exist.
    # exist_ok=True prevents an error if the directory is already there.
    os.makedirs(output_dir, exist_ok=True)
    
    # os.path.join creates a file path that is compatible with any OS (Windows, Mac, Linux).
    output_path = os.path.join(output_dir, f"mixed_population_dataset_{NUM_HOUSEHOLDS_TO_SIMULATE}_households_more_leaks.csv")
    
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




