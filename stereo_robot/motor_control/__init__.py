try:
    from .dual_shock_controller import client as DS4Client
    from .sabertooth import server as SabertoothServer
    from .direction_control import DirectionControl
except:
    from ..stereo_robot.calibration import Config
    print("uh oh")
