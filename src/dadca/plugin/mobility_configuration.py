from dataclasses import dataclass


@dataclass
class MobilityConfiguration:
    speed: float = 5
    tolerance: float = 0.5