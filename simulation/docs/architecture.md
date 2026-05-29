# Simulation Architecture

This document describes the simulation package boundaries and current launch flow.

## Existing Project Areas

```text
manual_control/        existing Python app, unchanged by simulation work
esp32cam_robot/        existing ESP32-CAM firmware, unchanged by simulation work
auto_soccer_bot/       existing automatic mode code, unchanged by simulation work
simulation/ros2_ws/    new ROS 2 simulation workspace
```

## Current Simulation Flow

```text
footbot_bringup -> starts Gazebo world
footbot_bringup -> starts robot_state_publisher
footbot_bringup -> starts joint_state_publisher
footbot_bringup -> starts ros_gz_bridge
footbot_bringup -> starts footbot_bridge HTTP server
footbot_bringup -> spawns footbot from /robot_description
footbot_description -> provides Xacro model, diff-drive plugin config, and camera sensor
footbot_gazebo -> provides SDF worlds, including a camera test scene
manual_control-compatible HTTP /move -> footbot_bridge -> ROS /cmd_vel
computer webcam -> footbot_perception -> ROS /gesture/direction
computer webcam -> footbot_perception -> ROS /gesture/speed
ROS gesture topics -> footbot_control -> ROS /cmd_vel
ROS /cmd_vel -> ros_gz_bridge -> Gazebo /cmd_vel -> DiffDrive plugin
Gazebo /odom -> ros_gz_bridge -> ROS /odom
Gazebo camera sensor -> ros_gz_bridge -> ROS /camera/image_raw
Gazebo camera info -> ros_gz_bridge -> ROS /camera/camera_info
```

## Planned Integration Flow

```text
manual_control -> footbot_bridge -> /cmd_vel -> simulated robot
webcam -> footbot_perception -> footbot_control -> /cmd_vel -> simulated robot
robot camera -> future object perception -> future autonomous behavior
footbot_bringup -> future startup orchestration
footbot_description -> future robot model assets
footbot_gazebo -> future Gazebo assets and integration
```

## Current Boundaries

The simulation currently creates a differential-drive model that accepts standard ROS 2 velocity commands.
It also provides an HTTP `/move` compatibility bridge for legacy clients.
The robot model includes a simulated camera mounted on `camera_link` and publishes camera data through ROS 2 topics.
The simulation workspace also contains a first ROS-native webcam gesture-control pipeline.

Not implemented yet:

- Object detection migration
- Changes to existing firmware or control applications
