from enum import Enum, auto


class Agent(Enum):
    ENERGY_STATION = auto()
    GROUND_STATION = auto()
    SENSOR = auto()
    UAV = auto()


class Timer(Enum):
    BATTERY_RECHARGE = "BATTERY_RECHARGE"
    HEARTBEAT = "HEARTBEAT"