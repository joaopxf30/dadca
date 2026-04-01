import logging

from gradysim.protocol.interface import IProtocol
from gradysim.protocol.messages.communication import SendMessageCommand
from gradysim.protocol.messages.telemetry import Telemetry

from src.dadca.constant import Agent
from src.dadca.domain.default_message import DefaultMessage
from src.dadca.domain.sender import Sender


class EnergyStationProtocol(IProtocol):
    _log: logging.Logger
    lamport_clock: float

    def initialize(self) -> None:
        self._log = logging.getLogger()
        self.lamport_clock = 0

    def handle_timer(self, timer: str) -> None:
        pass

    def handle_packet(self, message: str) -> None:
        default_message = DefaultMessage.model_validate_json(message)
        self._update_clock_on_receive(default_message.lamport_clock)

        if default_message.sender.agent == Agent.UAV:
            self.lamport_clock += 1
            response = DefaultMessage.model_construct(
                lamport_clock=self.lamport_clock,
                sender=Sender.model_construct(
                    agent=Agent.ENERGY_STATION,
                    id=self.provider.get_id()
                ),
            )
            command = SendMessageCommand(response.model_dump_json(), default_message.sender.id)
            self.provider.send_communication_command(command)

    def _update_clock_on_receive(self, lamport_clock: int) -> None:
        new_lamport_cock = max(self.lamport_clock, lamport_clock) + 1
        self.lamport_clock = new_lamport_cock

    def handle_telemetry(self, telemetry: Telemetry) -> None:
        pass

    def finish(self) -> None:
        pass