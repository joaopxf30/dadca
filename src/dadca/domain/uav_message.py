from src.dadca.domain.default_message import DefaultMessage


class UAVMessage(DefaultMessage):
    packet_count: int
    do_rendezvous: bool
    battery: float