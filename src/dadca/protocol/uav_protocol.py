import logging

from gradysim.protocol.interface import IProtocol
from gradysim.protocol.messages.communication import BroadcastMessageCommand
from gradysim.protocol.messages.telemetry import Telemetry

from src.dadca.constant import Agent
from src.dadca.dadca_mobility_configuration import DadcaMobilityConfiguration
from src.dadca.domain.default_message import DefaultMessage
from src.dadca.domain.sender import Sender
from src.dadca.dadca_mobility_plugin import DADCAMobilityPlugin


initial_waypoints = [3, 0]
PATH = [(0, 0, 20), (100, 0, 20), (200, 0, 20), (300, 0, 20), (400, 0, 20)]


class UAVProtocol(IProtocol):
    _log: logging.Logger
    _dadca: DADCAMobilityPlugin
    packet_count: int

    def initialize(self) -> None:
        self._log = logging.getLogger()
        self._dadca = DADCAMobilityPlugin(self, DadcaMobilityConfiguration())

        self._dadca.start_mission(
            initial_waypoint=initial_waypoints.pop(),
            path=PATH
        )

        self.packet_count = 0
        self._send_heartbeat()

    def _send_heartbeat(self) -> None:
        default_message = DefaultMessage.model_construct(
            packet_count=self.packet_count,
            sender=Sender.model_construct(
                agent=Agent.UAV,
                id=self.provider.get_id()
            )
        )
        command = BroadcastMessageCommand(default_message.model_dump_json())
        self.provider.send_communication_command(command)

        self.provider.schedule_timer("", self.provider.current_time() + 1)

    def handle_timer(self, timer: str) -> None:
        self._send_heartbeat()

    def handle_packet(self, message: str) -> None:
        default_message = DefaultMessage.model_validate_json(message)

        if default_message.sender.agent == Agent.SENSOR:
            self.packet_count += default_message.packet_count
        elif default_message.sender.agent == Agent.UAV:
            self.packet_count += default_message.packet_count
            self._dadca.execute_rendezvous()
        elif default_message.sender.agent == Agent.GROUND_STATION:
            self.packet_count = 1
        else:
            raise NotImplementedError(f"There is no current support to agent {default_message.sender.agent}")

    def handle_telemetry(self, telemetry: Telemetry) -> None:
        pass

    def finish(self) -> None:
        pass