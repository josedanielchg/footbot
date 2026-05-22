# Simulation Workspace

This document describes the ROS 2 workspace used by the Footbot simulation.

## Paths

- Workspace root: `simulation/ros2_ws`
- Source directory: `simulation/ros2_ws/src`
- Generated build artifacts: `simulation/ros2_ws/build`, `simulation/ros2_ws/install`, `simulation/ros2_ws/log`

The generated build artifact directories are ignored by `simulation/.gitignore`.

## Packages

| Package | Build type | Role |
| --- | --- | --- |
| `footbot_description` | `ament_cmake` | Robot description, Xacro model, frame definitions, and RViz config. |
| `footbot_gazebo` | `ament_cmake` | Gazebo world and simulation resources. |
| `footbot_bringup` | `ament_cmake` | Launch and orchestration for the simulation. |
| `footbot_control` | `ament_python` | Future ROS 2 command-mapping nodes. |
| `footbot_perception` | `ament_python` | Future camera, image-processing, and object-detection nodes. |
| `footbot_bridge` | `ament_python` | Future HTTP-to-ROS compatibility adapter. |

## Build

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot
source /opt/ros/humble/setup.bash
cd simulation/ros2_ws
colcon build --symlink-install
```

## Source

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
```

## Check Package Visibility

```bash
ros2 pkg list | grep footbot
```

Expected packages:

```text
footbot_bridge
footbot_bringup
footbot_control
footbot_description
footbot_gazebo
footbot_perception
```

Only the description, Gazebo, and bringup packages provide runtime resources at this point. Control, perception, and bridge packages are placeholders for future simulation work.
