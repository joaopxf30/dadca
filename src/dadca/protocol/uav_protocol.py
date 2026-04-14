import logging

from gradysim.protocol.interface import IProtocol
from gradysim.protocol.messages.communication import BroadcastMessageCommand
from gradysim.protocol.messages.mobility import GotoCoordsMobilityCommand
from gradysim.protocol.messages.telemetry import Telemetry
from pydantic.v1.validators import uuid_validator

from src.dadca.config import initial_waypoints, PATH, ENERGY_STATION_POSITION, RADIUS
from src.dadca.constant import Agent, Timer
from src.dadca.domain.package_message import PacketMessage
from src.dadca.plugin.battery_configuration import BatteryConfiguration
from src.dadca.plugin.battery_plugin import BatteryPlugin
from src.dadca.plugin.mobility_configuration import MobilityConfiguration
from src.dadca.domain.uav_message import UAVMessage
from src.dadca.domain.default_message import Sender, DefaultMessage
from src.dadca.plugin.mobility_plugin import MobilityPlugin
from src.geometry.point import Point


class UAVProtocol(IProtocol):
    _log: logging.Logger
    _mobility_plugin: MobilityPlugin
    _battery_plugin: BatteryPlugin
    lamport_clock: int
    packet_count: int
    wait: float = 0

    @classmethod
    def delay(cls):
        cls.wait += 20

    def initialize(self) -> None:
        self._log = logging.getLogger()
        self._mobility_plugin = MobilityPlugin(self, MobilityConfiguration())
        self._battery_plugin = BatteryPlugin(self, BatteryConfiguration())

        self.packet_count = 0
        self.lamport_clock = 0

        self._start_flight()
        self._send_heartbeat()

    def handle_timer(self, timer: str) -> None:
        if timer == Timer.HEARTBEAT.value:
            self._send_heartbeat()

        elif timer == Timer.START_MISSION.value:
            self._mobility_plugin.start_mission(
                initial_waypoint=initial_waypoints.pop(),
                path=PATH,
            )

        elif timer == Timer.BATTERY.value:
            self._move_to_waiting_area_energy_station()

        elif timer == Timer.CLEAR_RENDEZVOUS.value:
            self._mobility_plugin.ready_to_rendesvouz = True

        else:
            raise NotImplementedError(f"There is no current support to timer {timer}")

    def handle_packet(self, message: str) -> None:
        default_message = DefaultMessage.model_validate_json(message)
        self._update_clock_on_receive(default_message.lamport_clock)

        if default_message.sender.agent == Agent.SENSOR:
            message = PacketMessage.model_validate_json(message)
            self.packet_count += message.packet_count

        elif default_message.sender.agent == Agent.UAV:
            message = UAVMessage.model_validate_json(message)

            if self._mobility_plugin.on_mission:
                self.packet_count += message.packet_count

                if self._is_rendezvous():
                    self._execute_rendezvous()
                    self.provider.schedule_timer(
                        Timer.CLEAR_RENDEZVOUS.value,
                        self.provider.current_time() + 2
                    )

        elif default_message.sender.agent == Agent.GROUND_STATION:
            self.packet_count = 0

        elif default_message.sender.agent == Agent.ENERGY_STATION:
            self._broadcast()

        else:
            raise NotImplementedError(f"There is no current support to agent {default_message.sender.agent}")

    def handle_telemetry(self, telemetry: Telemetry) -> None:
        pass

    def _start_flight(self):
        self.provider.schedule_timer(
            Timer.START_MISSION.value,
            self.provider.current_time() + self.wait
        )
        self.delay()

    def _send_heartbeat(self) -> None:
        self._broadcast()
        self.provider.schedule_timer(
            Timer.HEARTBEAT.value,
            self.provider.current_time() + 1
        )

    def _broadcast(self):
        self.lamport_clock += 1
        uav_message = UAVMessage.model_construct(
            lamport_clock=self.lamport_clock,
            packet_count=self.packet_count,
            do_rendezvous=False,
            battery=self._battery_plugin.battery,
            sender=Sender.model_construct(
                agent=Agent.UAV,
                id=self.provider.get_id()
            )
        )
        command = BroadcastMessageCommand(uav_message.model_dump_json())
        self.provider.send_communication_command(command)

    def _update_clock_on_receive(self, lamport_clock: int) -> None:
        new_lamport_cock = max(self.lamport_clock, lamport_clock) + 1
        self.lamport_clock = new_lamport_cock

    def _is_rendezvous(self) -> bool:
        return self._mobility_plugin.ready_to_rendesvouz

    def _execute_rendezvous(self) -> None:
        self._mobility_plugin.reverse_direction()
        self._mobility_plugin.change_current_waypoint()
        self._mobility_plugin.travel_to_current_waypoint()
        self._mobility_plugin.ready_to_rendesvouz = False

    def _move_to_waiting_area_energy_station(self) -> None:
        self._mobility_plugin.on_mission = False

        current_point = self._battery_plugin.critical_battery_position
        direction = current_point - ENERGY_STATION_POSITION
        waiting_point = ENERGY_STATION_POSITION + direction * (RADIUS/direction.compute_euclidean_norm())

        mobility_command = GotoCoordsMobilityCommand(*waiting_point)
        self.provider.send_mobility_command(mobility_command)

    def _enter_energy_station(self):
        mobility_command = GotoCoordsMobilityCommand(*ENERGY_STATION_POSITION)
        self.provider.send_mobility_command(mobility_command)

    def finish(self) -> None:
        self._log.info(f"Final Lamport clock: {self.lamport_clock}")