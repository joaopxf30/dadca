from gradysim.simulator.handler.communication import CommunicationHandler, CommunicationMedium
from gradysim.simulator.handler.mobility import MobilityHandler

from gradysim.simulator.handler.timer import TimerHandler
from gradysim.simulator.handler.visualization import VisualizationHandler, VisualizationConfiguration
from gradysim.simulator.simulation import SimulationBuilder, SimulationConfiguration

from src.dadca.protocol.ground_station_protocol import GroundStationProtocol
from src.dadca.protocol.sensor_protocol import SensorProtocol
from src.dadca.protocol.uav_protocol import UAVProtocol


def main():
    config = SimulationConfiguration(
        duration=30
    )
    builder = SimulationBuilder(config)

    # Instantiating 4 sensors in fixed positions
    builder.add_node(SensorProtocol, (100, 0, 0))
    builder.add_node(SensorProtocol, (200, 0, 0))
    builder.add_node(SensorProtocol, (300, 0, 0))
    builder.add_node(SensorProtocol, (400, 0, 0))

    PATH = [(0, 0, 20), (100, 0, 20), (200, 0, 20), (300, 0, 20), (400, 0, 20)]

    # Instantiating 1 UAVs at (0,0,0)
    builder.add_node(UAVProtocol, (0, 0, 0))

    # Instantiating ground station at (0,0,0)
    builder.add_node(GroundStationProtocol, (0, 0, 0))

    # Adding required handlers
    builder.add_handler(TimerHandler())
    builder.add_handler(CommunicationHandler(CommunicationMedium(
        transmission_range=30
    )))
    builder.add_handler(MobilityHandler())
    builder.add_handler(VisualizationHandler(VisualizationConfiguration(
        x_range=(0, 400),
        y_range=(-150, 150),
        z_range=(0, 150)
    )))

    # Building & starting
    simulation = builder.build()
    simulation.start_simulation()


if __name__ == "__main__":
    main()
