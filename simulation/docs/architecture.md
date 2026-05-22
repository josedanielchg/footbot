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
footbot_bringup -> spawns footbot from /robot_description
footbot_description -> provides minimal Xacro model
footbot_gazebo -> provides minimal SDF world
```

## Planned Integration Flow

```text
manual_control -> footbot_bridge -> footbot_control -> simulated robot
footbot_perception -> future camera/object processing
footbot_bringup -> future startup orchestration
footbot_description -> future robot model assets
footbot_gazebo -> future Gazebo assets and integration
```

## Current Boundaries

The simulation currently creates and spawns a static model only.

Not implemented yet:

- Motion control
- Differential-drive plugin
- HTTP adapter
- `/cmd_vel` command mapping
- Camera sensor plugin
- OpenCV or MediaPipe migration
- Changes to existing firmware or control applications
