from dataclasses import dataclass


@dataclass
class BatteryConfiguration:
    battery_tolerance: float = 10
    discharge_per_meter_factor = 0.05