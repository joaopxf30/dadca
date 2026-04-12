from enum import Enum, auto


class Agent(Enum):
    ENERGY_STATION = auto()
    GROUND_STATION = auto()
    SENSOR = auto()
    UAV = auto()


class Timer(Enum):
    BATTERY = "BATTERY"
    HEARTBEAT = "HEARTBEAT"
    START_MISSION = "START_MISSION"


class Movement(Enum):
    FORWARD = 1
    BACKWARD = -1
