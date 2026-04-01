import logging

from gradysim.protocol.interface import IProtocol
from gradysim.protocol.messages.communication import BroadcastMessageCommand
from gradysim.protocol.messages.mobility import GotoCoordsMobilityCommand
from gradysim.protocol.messages.telemetry import Telemetry

from src.dadca.config import initial_waypoints, PATH, ENERGY_STATION_POSITION
from src.dadca.constant import Agent, Timer
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
    lamport_clock: int
    packet_count: int
    wait: float = 0

    def initialize(self) -> None:
        self._log = logging.getLogger()
        self._mobility_plugin = MobilityPlugin(self, MobilityConfiguration())
        self._battery_plugin = BatteryPlugin(self, BatteryConfiguration())

        self._battery_plugin.handle_battery(
            critical_battery_action=self.move_to_energy_station,
            recharge_battery_action=self.get_back_to_mission,
        )
        self._mobility_plugin.start_mission(
            initial_waypoint=initial_waypoints.pop(),
            path=PATH,
            wait=UAVProtocol.wait,
        )

        self.delay()
        self.packet_count = 0
        self.lamport_clock = 0

        self._send_heartbeat()

    @classmethod
    def delay(cls):
        cls.wait += 3

    def _send_heartbeat(self) -> None:
        self.lamport_clock += 1

        default_message = DefaultMessage.model_construct(
            packet_count=self.packet_count,
            lamport_clock=self.lamport_clock,
            sender=Sender.model_construct(
                agent=Agent.UAV,
                id=self.provider.get_id()
            )
        )
        command = BroadcastMessageCommand(default_message.model_dump_json())
        self.provider.send_communication_command(command)

        self.provider.schedule_timer(Timer.HEARTBEAT.value, self.provider.current_time() + 1)

    def handle_timer(self, timer: str) -> None:
        if timer == Timer.HEARTBEAT.value:
            self._send_heartbeat()

        elif timer == Timer.BATTERY_RECHARGE.value:
            self._battery_plugin.recharge_battery()

        else:
            raise NotImplementedError(f"There is no current support to timer {timer}")

    def handle_packet(self, message: str) -> None:
        default_message = DefaultMessage.model_validate_json(message)
        self._update_clock_on_receive(default_message.lamport_clock)

        if default_message.sender.agent == Agent.SENSOR:
            self.packet_count += default_message.packet_count

        elif default_message.sender.agent == Agent.UAV:
            if self._mobility_plugin.on_mission and not self._battery_plugin.is_critical_battery:
                self.packet_count += default_message.packet_count
                self.execute_rendezvous()

        elif default_message.sender.agent == Agent.GROUND_STATION:
            self.packet_count = 1

        elif default_message.sender.agent == Agent.ENERGY_STATION:
            # self.enter_energy_station()
            self._battery_plugin.recharge_battery()

        else:
            raise NotImplementedError(f"There is no current support to agent {default_message.sender.agent}")

    def _update_clock_on_receive(self, lamport_clock: int) -> None:
        new_lamport_cock = max(self.lamport_clock, lamport_clock) + 1
        self.lamport_clock = new_lamport_cock

    def execute_rendezvous(self) -> None:
        self._mobility_plugin.reverse_direction()
        self._mobility_plugin.change_current_waypoint()
        self._mobility_plugin.travel_to_current_waypoint()

    def move_to_energy_station(self):
        self._mobility_plugin.on_mission = False
        mobility_command = GotoCoordsMobilityCommand(*ENERGY_STATION_POSITION)
        self.provider.send_mobility_command(mobility_command)

    def enter_energy_station(self):
        mobility_command = GotoCoordsMobilityCommand(*ENERGY_STATION_POSITION)
        self.provider.send_mobility_command(mobility_command)

    def get_back_to_mission(self):
        self._mobility_plugin.start_mission(
            initial_waypoint=self._mobility_plugin.current_waypoint,
            path=PATH
        )

    def handle_telemetry(self, telemetry: Telemetry) -> None:
        pass

    def finish(self) -> None:
        self._log.info(f"Final Lamport clock: {self.lamport_clock}")