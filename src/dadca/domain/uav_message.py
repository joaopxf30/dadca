from src.dadca.domain.default_message import DefaultMessage


class UAVMessage(DefaultMessage):
    lamport_clock: int
    packet_count: int
    do_rendezvous: bool
    battery: float