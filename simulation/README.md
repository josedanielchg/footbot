# FootBot Simulation

This folder contains the ROS 2 + Gazebo simulation layer for FootBot. It is
isolated from the legacy ESP32 firmware and host-side control applications.

## Quick Start

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Launch the base robot simulation:

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py
```

Launch the current autonomous soccer behavior:

```bash
ros2 launch footbot_bringup ball_control.launch.py scenario:=front show_debug_view:=true
```

## Documentation

Start here:

- [Simulation docs index](docs/README.md)
- [Setup](docs/SETUP.md)
- [Workspace](docs/WORKSPACE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Simulation modes](docs/MODES.md)
- [Ball control](docs/BALL_CONTROL.md)

Reference guides:

- [Perception and datasets](docs/PERCEPTION_AND_DATASETS.md)
- [Worlds and scenarios](docs/WORLDS_AND_SCENARIOS.md)
- [Planned soccer stages](docs/PLANNED_SOCCER_STAGES.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Development guide](docs/DEVELOPMENT_GUIDE.md)

## Current Packages

```text
footbot_common           shared constants and tiny utilities
footbot_description      robot Xacro model and frames
footbot_gazebo           worlds, models, bridge config, Gazebo plugins
footbot_bringup          launch orchestration
footbot_bridge           HTTP /move compatibility bridge
footbot_perception       webcam, hand, HSV ball detection, debug viewer
footbot_control          gesture and simple ball-following controllers
footbot_soccer_msgs      custom soccer behavior messages
footbot_soccer_behavior  ball-control estimator, skills, and FSM
footbot_soccer_vision    YOLO perception and dataset tools
```

## Control Rule

Run only one `/cmd_vel` owner at a time. Manual/HTTP, gesture control, simple
ball following, and deterministic ball control are separate modes.

## Legacy Code Boundaries

These folders remain available as references and should not be modified by
simulation work unless a future task explicitly requires it:

```text
esp32cam_robot/
manual_control/
auto_soccer_bot/
soccer_vision/
```
