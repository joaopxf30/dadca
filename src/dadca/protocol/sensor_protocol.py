import logging

from gradysim.protocol.interface import IProtocol
from gradysim.protocol.messages.communication import SendMessageCommand
from gradysim.protocol.messages.telemetry import Telemetry

from src.dadca.domain.default_message import DefaultMessage
from src.dadca.domain.sender import Sender

from src.dadca.constant import Agent


class SensorProtocol(IProtocol):
    _log: logging.Logger
    packet_count: int

    def initialize(self) -> None:
        self._log = logging.getLogger()
        self.packet_count = 0

        self._generate_packet()

    def _generate_packet(self) -> None:
        self.packet_count += 1
        self._log.info(f"Generated packet, current count {self.packet_count}")
        self.provider.schedule_timer("", self.provider.current_time() + 1)

    def handle_timer(self, timer: str) -> None:
        self._generate_packet()

    def handle_packet(self, message: str) -> None:
        default_message = DefaultMessage.model_validate_json(message)

        if default_message.sender.agent == Agent.UAV:
            response = DefaultMessage.model_construct(
                package_count=self.packet_count,
                sender=Sender.model_construct(
                    agent=Agent.SENSOR,
                    id=self.provider.get_id()
                ),
            )
            command = SendMessageCommand(response.model_dump_json(), default_message.sender.id)
            self.provider.send_communication_command(command)

            logging.info(f"Sent {response.package_count} packets to UAV {default_message.sender.id}")

            self.packet_count = 0

    def handle_telemetry(self, telemetry: Telemetry) -> None:
        pass

    def finish(self) -> None:
        pass
