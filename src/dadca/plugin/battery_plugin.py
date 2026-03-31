import logging
from typing import Callable

from gradysim.protocol.interface import IProtocol
from gradysim.protocol.messages.telemetry import Telemetry
from gradysim.protocol.plugin.dispatcher import create_dispatcher
from gradysim.protocol.position import squared_distance, Position

from src.dadca.config import ENERGY_STATION_POSITION
from src.dadca.plugin.battery_configuration import BatteryConfiguration


class BatteryPlugin:
    def __init__(self, protocol: IProtocol, configuration: BatteryConfiguration):
        self._dispatcher = create_dispatcher(protocol)
        self._instance = protocol
        self._configuration = configuration
        self._logger = logging.getLogger()

        self._previous_position: Position | None = None
        self._is_critical_battery = False
        self._battery: float = 100

        self._critical_battery_action: Callable | None = None
        self._recharge_battery_scenario: Callable | None = None

    def _initialize_telemtry_handling(self):
        def telemetry_handler(_instance: IProtocol, telemetry: Telemetry) -> None:
            current_position = telemetry.current_position

            if self._previous_position is not None:
                battery_cost = self._compute_battery_cost(self._previous_position, current_position)
                self._battery -= battery_cost

                if (
                    self._is_critical_battery is False
                    and self._has_reached_critical_battery(current_position)
                ):
                    self._is_critical_battery = True

                    if self._critical_battery_action is None:
                        raise RuntimeError("Critical battery action not set yet")

                    self._logger.info("Critical battery has been reached. Agent is moving to Energy Station")
                    self._critical_battery_action()

            self._previous_position = current_position

        self._dispatcher.register_handle_telemetry(telemetry_handler)

    def _has_reached_critical_battery(self, current_position: Position) -> bool:
        """
        Check if battery station is reacheable

        """
        battery_cost = self._compute_battery_cost(current_position, ENERGY_STATION_POSITION)

        self._logger.info(f"{self._battery} <= {battery_cost} + {self._configuration.battery_tolerance}")

        return self._battery <= battery_cost + self._configuration.battery_tolerance

    def _compute_battery_cost(self, current_position: Position, target_position: Position) -> float:
        distance = squared_distance(current_position, target_position) ** 0.5
        battery_cost = distance * self._configuration.discharge_per_meter_factor

        return battery_cost

    def handle_battery(
        self,
        critical_battery_action: Callable,
        recharge_battery_action: Callable | None,
    ):
        self._critical_battery_action = critical_battery_action
        self._recharge_battery_scenario = recharge_battery_action

        self._initialize_telemtry_handling()