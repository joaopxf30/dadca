import logging
from enum import Enum
from typing import Optional

from gradysim.protocol.interface import IProtocol
from gradysim.protocol.messages.mobility import SetSpeedMobilityCommand, GotoCoordsMobilityCommand
from gradysim.protocol.messages.telemetry import Telemetry
from gradysim.protocol.plugin.dispatcher import create_dispatcher, DispatchReturn
from gradysim.protocol.plugin.mission_mobility import MissionMobilityConfiguration
from gradysim.protocol.position import Position, squared_distance


class Movement(Enum):
    FORWARD = 1
    BACKWARD = -1

class DADCAMobilityPlugin:
    _MISSION: Optional[list[Position]] = None

    @classmethod
    def set_map(cls, mission: list[Position]):
        cls._MISSION = mission

    def __init__(
        self,
        protocol: IProtocol,
    ):
        self._dispatcher = create_dispatcher(protocol)
        self._instance = protocol
        self._logger = logging.getLogger()

        self._current_waypoint: Optional[int] = None
        self._current_direction: Optional[Movement] = None

    def _initialize_telemetry_handling(self):
        def telemetry_handler(_instance: IProtocol, telemetry: Telemetry):
            if self._MISSION is None:
                return DispatchReturn.CONTINUE

            if self._has_reached_target(telemetry.current_position):
                self._progress_current_waypoint()
                self._travel_to_current_waypoint()

        self._dispatcher.register_handle_telemetry(telemetry_handler)

    def _has_reached_target(self, current_position: Position) -> bool:
        target_position = self._MISSION[self._current_waypoint]

        return squared_distance(current_position, target_position) <= self._configuration.tolerance ** 2

    def _progress_current_waypoint(self) -> None:
        if (
            self._current_waypoint == len(self._MISSION)
            or self._current_waypoint == 0
        ):
            self._reverse_direction()

        self._change_current_waypoint()

    def _reverse_direction(self) -> None:
        if self._current_direction == Movement.FORWARD:
            self._current_direction = Movement.BACKWARD

        else:
            self._current_direction = Movement.FORWARD

    def _change_current_waypoint(self) -> None:
        self._current_waypoint += self._current_direction.value

    def _travel_to_current_waypoint(self) -> None:
        if self._current_waypoint is None:
            return

        mobility_command = GotoCoordsMobilityCommand(*self._MISSION[self._current_waypoint])
        self._instance.provider.send_mobility_command(mobility_command)

    def start_mission(
        self,
        start_position: Position,
    ) -> None:
        """
        Send the UAVs to the initial position to start collecting data from the sensors.

        """
        self._initialize_telemetry_handling()


        speed_command = SetSpeedMobilityCommand(self._configuration.speed)
        self._instance.provider.send_mobility_command(speed_command)

    def execute_rendezvous(self) -> None:
        self._reverse_direction()
        self._change_current_waypoint()
        self._travel_to_current_waypoint()
