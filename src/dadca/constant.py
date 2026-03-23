from enum import Enum, auto


class Agent(Enum):
    GROUND_STATION = auto()
    SENSOR = auto()
    UAV = auto()
