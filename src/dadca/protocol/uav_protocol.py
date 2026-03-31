import logging

from gradysim.protocol.interface import IProtocol
from gradysim.protocol.messages.communication import BroadcastMessageCommand
from gradysim.protocol.messages.mobility import GotoCoordsMobilityCommand
from gradysim.protocol.messages.telemetry import Telemetry

from src.dadca.config import initial_waypoints, PATH, ENERGY_STATION_POSITION
from src.dadca.constant import Agent
from src.dadca.plugin.battery_configuration import BatteryConfiguration
from src.dadca.plugin.battery_plugin import BatteryPlugin
from src.dadca.plugin.mobility_configuration import MobilityConfiguration
from src.dadca.domain.default_message import DefaultMessage
from src.dadca.domain.sender import Sender
from src.dadca.plugin.mobility_plugin import MobilityPlugin


class UAVProtocol(IProtocol):
    _log: logging.Logger
    _mobility_plugin: MobilityPlugin
    _battery_plugin: BatteryPlugin
    packet_count: int

    def initialize(self) -> None:
        self._log = logging.getLogger()
        self._mobility_plugin = MobilityPlugin(self, MobilityConfiguration())
        self._battery_plugin = BatteryPlugin(self, BatteryConfiguration())

        self._battery_plugin.handle_battery(
            critical_battery_action=self.move_to_energy_station,
            recharge_battery_action=None,
        )
        self._mobility_plugin.start_mission(
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
            self._mobility_plugin.execute_rendezvous()
        elif default_message.sender.agent == Agent.GROUND_STATION:
            self.packet_count = 1
        else:
            raise NotImplementedError(f"There is no current support to agent {default_message.sender.agent}")

    def move_to_energy_station(self):
        mobility_command = GotoCoordsMobilityCommand(*ENERGY_STATION_POSITION)
        self.provider.send_mobility_command(mobility_command)

    def handle_telemetry(self, telemetry: Telemetry) -> None:
        pass

    def finish(self) -> None:
        pass