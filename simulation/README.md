# Footbot Simulation

This folder contains the ROS 2 and Gazebo simulation work for the Footbot project.

The simulation workspace is intentionally isolated from the existing ESP32-CAM firmware, manual control application, automatic control code, and HTTP robot API.

## Selected Stack

- Ubuntu: 22.04.4 LTS (`jammy`)
- Architecture: `x86_64`
- ROS 2: Humble Hawksbill
- Gazebo: Fortress
- ROS/Gazebo integration: `ros-humble-ros-gz`

## Documents

- [Stack decision](docs/STACK_DECISION.md)
- [Ubuntu 22.04 installation](docs/INSTALL_UBUNTU_22_04.md)
- [Verification steps](docs/VERIFICATION.md)
- [Workspace guide](docs/workspace.md)
- [Architecture](docs/architecture.md)

## Workspace

The ROS 2 workspace lives at:

```bash
simulation/ros2_ws
```

Build it with:

```bash
cd simulation/ros2_ws
colcon build --symlink-install
```

Source it with:

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
```

## Packages

- `footbot_description`: Xacro model, frame structure, and Gazebo diff-drive plugin configuration.
- `footbot_gazebo`: Gazebo world and ROS/Gazebo bridge reference configuration.
- `footbot_bringup`: launch flow for starting Gazebo, publishing the robot description, spawning the robot, and bridging movement topics.
- `footbot_control`: future control nodes and command mapping.
- `footbot_perception`: future camera, image processing, and object detection nodes.
- `footbot_bridge`: future compatibility adapter for the existing HTTP-oriented control flow.

## Launch

Build and source the workspace:

```bash
cd simulation/ros2_ws
colcon build --symlink-install
source /opt/ros/humble/setup.bash
source install/setup.bash
```

Launch the robot in Gazebo:

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py
```

For a server-only run without the Gazebo GUI:

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py use_gui:=false
```

Send a simple forward velocity command:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.12, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

Stop the robot:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```
