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
- [Simulation reference](docs/SIMULATION_REFERENCE.md)

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

- `footbot_description`: Xacro model, frame structure, Gazebo diff-drive plugin configuration, and robot-mounted camera sensor.
- `footbot_gazebo`: Gazebo worlds and ROS/Gazebo bridge reference configuration.
- `footbot_bringup`: launch flow for Gazebo, robot spawning, topic bridges, HTTP control, gesture control, and autonomous ball following.
- `footbot_control`: ROS-native gesture-to-velocity and ball-following command mapping.
- `footbot_perception`: webcam publishing, MediaPipe hand detection, gesture classification, and OpenCV ball detection.
- `footbot_bridge`: ESP32-compatible HTTP `/move` adapter for publishing simulation velocity commands.
- `footbot_soccer_msgs`: custom soccer behavior messages such as `BallState`.
- `footbot_soccer_behavior`: deterministic ball-control state estimation, skills, and FSM.
- `footbot_soccer_vision`: YOLO-based soccer vision experiments, opponent detections, debug visualization, and dataset capture.

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

The launch starts the HTTP bridge by default at:

```text
http://127.0.0.1:8080
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

Or send an ESP32-compatible HTTP command:

```bash
curl -s -X POST http://127.0.0.1:8080/move \
  -H 'Content-Type: application/json' \
  -d '{"direction":"forward","speed":150}'
```

Check the HTTP bridge:

```bash
curl -s http://127.0.0.1:8080/status
```

Check camera topics:

```bash
ros2 topic list | grep camera
ros2 topic info /camera/image_raw
ros2 topic info /camera/camera_info
```

View the simulated robot camera:

```bash
rqt_image_view /camera/image_raw
```

## ROS-Native Gesture Control

Install the MediaPipe/NumPy versions used by the gesture detector:

```bash
python3 -m pip install --user --force-reinstall "numpy==1.26.4" "mediapipe==0.10.14"
```

Launch the full simulation with webcam gesture control:

```bash
ros2 launch footbot_bringup sim_gesture_control.launch.py
```

Launch with a local MediaPipe-style debug window:

```bash
ros2 launch footbot_bringup sim_gesture_control.launch.py show_debug_view:=true
```

Run only gesture perception:

```bash
ros2 launch footbot_bringup gesture_perception.launch.py
```

Run only gesture-to-velocity control:

```bash
ros2 launch footbot_bringup gesture_control.launch.py
```

ROS-native gesture topics:

```text
/webcam/image_raw
/gesture/direction
/gesture/speed
/gesture/debug_image
```

## Autonomous Ball Following

Launch the autonomous simulation mode:

```bash
ros2 launch footbot_bringup ball_following.launch.py
```

Launch with the ball detector debug window:

```bash
ros2 launch footbot_bringup ball_following.launch.py show_debug_view:=true
```

Ball follower topics:

```text
/camera/image_raw
/ball_detection
/ball/debug_image
/cmd_vel
```

Only run one `/cmd_vel` owner at a time. Use separate launch modes for HTTP/manual control, gesture control, and autonomous ball following.

The default detector uses HSV orange segmentation with a permissive circularity threshold tuned for the simulated camera view.

## Soccer Ball Control

Launch the deterministic one-robot ball-control behavior:

```bash
ros2 launch footbot_bringup ball_control.launch.py
```

Launch a specific scenario with a debug image window:

```bash
ros2 launch footbot_bringup ball_control.launch.py scenario:=left show_debug_view:=true
```

Available scenarios:

```text
front
left
right
far
close
misaligned
```

Ball-control topics:

```text
/camera/image_raw
/ball_detection
/ball/debug_image
/soccer/ball_state
/soccer/fsm_state
/cmd_vel
```

This mode uses the HSV ball detector, a `BallState` estimator, and a finite-state
machine. It does not implement shooting, opponent interaction, team play, or RL.

Launch the multi-lane ball-control stress test:

```bash
ros2 launch footbot_bringup ball_control_multi.launch.py
```

This starts three wall-separated lanes in one Gazebo world:

```text
front   robot faces a ball in front of it
far     robot faces a farther ball
behind  robot starts with the ball behind it and must search by rotating
```

Each lane has isolated topics under `/ball_control/<lane>/`, for example
`/ball_control/front/camera/image_raw`, `/ball_control/front/ball_detection`,
`/ball_control/front/soccer/ball_state`, and `/ball_control/front/cmd_vel`.

## YOLO Opponent Detection

Install the optional YOLO dependencies from the repository root:

```bash
python3 -m pip install --user -r simulation/requirements-yolo.txt
```

Launch the opponent-detection simulation mode:

```bash
ros2 launch footbot_bringup opponent_detection.launch.py
```

Launch with the debug image window:

```bash
ros2 launch footbot_bringup opponent_detection.launch.py show_debug_view:=true
```

Opponent detection topics:

```text
/camera/image_raw
/opponent_detections
/opponent_detection/debug_image
```

The default YOLO model is `yolo11n.pt` with `target_classes:=person`. This is
for inference plumbing and dataset capture. Reliable detection of custom Gazebo
  FootBot-like opponent placeholders will require fine-tuning later.
The dependency file pins Ultralytics to `8.4.56`, the current non-yanked PyPI
release verified on 2026-05-30.

Capture dataset images from the robot camera:

```bash
ros2 run footbot_soccer_vision image_capture \
  --ros-args -p image_topic:=/camera/image_raw
```

Only run one `/cmd_vel` owner at a time. Opponent detection mode does not command
the robot.

## Soccer Field Scene

Open the soccer field layout:

```bash
ros2 launch footbot_bringup soccer_field.launch.py
```

The scene contains:

- a small green field
- border walls to keep the ball inside
- two goals
- a dynamic ball at the center
- two mirrored teams of three FootBot-like robots

The robots are static placeholders for layout and perception work. Future work
can replace them with individually spawned controlled robots.

Run soccer-field detection from the blue goalkeeper camera:

```bash
ros2 launch footbot_bringup soccer_detection.launch.py show_debug_view:=true
```

Camera and detector topics:

```text
/soccer/camera/image_raw
/soccer/camera/camera_info
/opponent_detections
/goal_detections
```

The default `yolo11n.pt` model can verify the YOLO/ROS pipeline, but it does not
know custom `goal` or `opponent robot` classes. Use custom trained weights when
they are ready:

```bash
ros2 launch footbot_bringup soccer_detection.launch.py model_path:=/path/to/best.pt
```
