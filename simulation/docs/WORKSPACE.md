# Workspace

The ROS 2 workspace lives at:

```text
simulation/ros2_ws/
```

Generated folders are ignored by Git:

```text
simulation/ros2_ws/build/
simulation/ros2_ws/install/
simulation/ros2_ws/log/
```

## Packages

| Package | Build type | Responsibility |
| --- | --- | --- |
| `footbot_common` | `ament_python` | Shared topic, frame, geometry, and math constants. |
| `footbot_description` | `ament_cmake` | Xacro robot model, frames, wheels, camera sensor, RViz config. |
| `footbot_gazebo` | `ament_cmake` | Gazebo worlds, models, bridge config, ball drag plugin. |
| `footbot_bringup` | `ament_cmake` | Launch orchestration for all simulation modes. |
| `footbot_bridge` | `ament_python` | ESP32-compatible HTTP `/move` to ROS `/cmd_vel`. |
| `footbot_perception` | `ament_python` | Webcam, hand detection, HSV ball detection, debug image viewer. |
| `footbot_control` | `ament_python` | Gesture-to-velocity and simple ball-follower controllers. |
| `footbot_soccer_msgs` | `ament_cmake` | Custom soccer behavior messages such as `BallState`. |
| `footbot_soccer_behavior` | `ament_python` | Ball-control state estimation, skills, and FSM. |
| `footbot_soccer_vision` | `ament_python` | YOLO soccer perception, dataset capture, augmentation tools. |

## Build And Source

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Source `install/setup.bash` again after every build and in every new terminal.

## Useful Checks

```bash
colcon list --base-paths src
ros2 pkg executables footbot_perception
ros2 pkg executables footbot_soccer_behavior
ros2 launch footbot_bringup ball_control.launch.py --show-args
```
