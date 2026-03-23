from gradysim.protocol.interface import IProtocol
from gradysim.protocol.messages.telemetry import Telemetry


class UAVProtocol(IProtocol):
    def initialize(self) -> None:
        pass

    def handle_timer(self, timer: str) -> None:
        pass

    def handle_packet(self, message: str) -> None:
        pass

    def handle_telemetry(self, telemetry: Telemetry) -> None:
        pass

    def finish(self) -> None:
        pass