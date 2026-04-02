from src.dadca.constant import Movement
from src.dadca.domain.default_message import DefaultMessage


class UAVMessage(DefaultMessage):
    lamport_clock: int
    packet_count: int
    waypoint: int | None
    movement: Movement | None
    battery: float