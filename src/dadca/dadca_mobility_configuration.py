from dataclasses import dataclass


@dataclass
class DadcaMobilityConfiguration:
    speed: float = 5
    tolerance: float = 0.5