from gradysim.protocol.interface import IProtocol
from gradysim.protocol.messages.communication import SendMessageCommand
from gradysim.protocol.messages.telemetry import Telemetry

from src.dadca.constant import Agent
from src.dadca.domain.default_message import DefaultMessage
from src.dadca.domain.sender import Sender


class GroundStationProtocol(IProtocol):
    packet_count: int

    def initialize(self) -> None:
        self.packet_count = 0

    def handle_timer(self, timer: str) -> None:
        pass

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

            command = SendMessageCommand(response.model_dump_json(), default_message.agent.value)
            self.provider.send_communication_command(command)

            self._log.info(f"Sent {response['packet_count']} packets to UAV {simple_message['sender']}")

            self.packet_count = 0

    def handle_telemetry(self, telemetry: Telemetry) -> None:
        pass

    def finish(self) -> None:
        pass