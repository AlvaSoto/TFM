from dataclasses import dataclass, field
from datetime import datetime, timedelta

'''
@dataclass: decorator that wraps my class and automates the creation of specific methods
like init, repr, eq

When i create a class with the wrapper i dont need to add the def __init__(self,..) it does

it for me 

'''

@dataclass
class WaterEvent:
    """It represents a unique comsuption event of water"""
    event_type: str
    start_time: datetime
    duration_minutes: float
    flow_rate_lpm: float
    household_id: str
    total_consumption_l: float=field(init=False) #this is a field i dont want to initialise, it is calculated after the init

    #This is what we can do with the wrapper, this method is executed after the event creation
    def __post_init__(self):
        self.total_consumption_l = self.duration_minutes * self.flow_rate_lpm


@dataclass
class LeakEvent:
    """Represents a Leak event for the ground of truth"""

    start_time: datetime
    end_time: datetime
    flow_rate_lpm: float
    household_id: str
    total_consumption_l: float=field(init=False)

    def __post_init__(self):
        duration_minutes = (self.end_time - self.start_time).total_seconds() / 60
        self.total_consumption_l = duration_minutes * self.flow_rate_lpm
