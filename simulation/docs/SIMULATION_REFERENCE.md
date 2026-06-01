# FootBot Simulation Reference

This document is a working reference for the ROS 2 and Gazebo simulation work in
`simulation/`. It is intentionally broader than the package READMEs: it explains
what has been built so far, why the folders exist, how the ROS 2 pieces fit
together, how Gazebo is used, and which commands are useful for running and
verifying each workflow.

This file is meant to be a source document for future official documentation and
project reports.

## Scope

The simulation layer is isolated under:

```text
simulation/
```

Existing project folders remain available as references and should not be
modified by simulation work unless a future task explicitly requires it:

```text
esp32cam_robot/     ESP32-CAM firmware and physical robot HTTP API
manual_control/     legacy Python gesture-control client
auto_soccer_bot/    existing automatic soccer scripts and model references
soccer_vision/      existing labeling, dataset, training, and YOLO notebooks
```

The simulation currently provides:

- a ROS 2 workspace
- a FootBot robot model
- Gazebo worlds
- ROS/Gazebo topic bridges
- differential-drive motion through `/cmd_vel`
- an ESP32-compatible HTTP `/move` bridge
- a simulated robot camera
- webcam gesture perception and ROS-native control
- autonomous HSV ball following
- deterministic one-robot soccer ball control
- YOLO opponent and goal detector plumbing
- a soccer field scene with walls, goals, a center ball, and mirrored teams

## Selected Stack

The selected stack is:

```text
Ubuntu 22.04 jammy
ROS 2 Humble Hawksbill
Gazebo Fortress
ros_gz integration packages
Python 3.10
```

Important ROS/Gazebo packages used by the simulation:

```text
ros_gz_sim
ros_gz_bridge
robot_state_publisher
joint_state_publisher
xacro
cv_bridge
sensor_msgs
geometry_msgs
nav_msgs
std_msgs
vision_msgs
```

Optional Python dependencies:

```text
MediaPipe and OpenCV for gesture perception
Ultralytics YOLO for soccer vision
```

## Installation

Install ROS 2 and Gazebo using the existing installation guide:

```text
simulation/docs/INSTALL_UBUNTU_22_04.md
```

After installation, source ROS 2:

```bash
source /opt/ros/humble/setup.bash
```

Useful baseline checks:

```bash
ros2 doctor
ros2 pkg list | grep ros_gz
ign gazebo --versions
```

Install optional gesture dependencies:

```bash
python3 -m pip install --user --force-reinstall "numpy==1.26.4" "mediapipe==0.10.14"
```

Install optional YOLO runtime dependencies:

```bash
python3 -m pip install --user -r simulation/requirements-yolo.txt
```

The YOLO requirements pin NumPy to `1.26.4` to avoid the NumPy 2.x ABI problem
that can break ROS/OpenCV/MediaPipe imports on Ubuntu 22.04.

## Workspace Layout

The ROS 2 workspace is:

```text
simulation/ros2_ws/
```

Important workspace folders:

```text
simulation/ros2_ws/src/       source packages
simulation/ros2_ws/build/     generated build files, ignored by Git
simulation/ros2_ws/install/   generated install space, ignored by Git
simulation/ros2_ws/log/       generated build/test logs, ignored by Git
```

Build the workspace:

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot
source /opt/ros/humble/setup.bash
cd simulation/ros2_ws
colcon build --symlink-install
```

Source the workspace after every build:

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
```

Check package visibility:

```bash
ros2 pkg list | grep footbot
```

Expected simulation packages:

```text
footbot_bridge
footbot_bringup
footbot_control
footbot_description
footbot_gazebo
footbot_perception
footbot_soccer_vision
```

## Package Roles

### `footbot_description`

Build type: `ament_cmake`

Purpose:

- owns the robot Xacro model
- defines core frames and links
- defines wheel joints
- embeds Gazebo diff-drive plugin configuration
- embeds the robot-mounted Gazebo camera sensor
- provides RViz configuration

Key files:

```text
footbot_description/urdf/footbot.urdf.xacro
footbot_description/rviz/footbot_model.rviz
```

Important frames:

```text
base_footprint
base_link
left_wheel_link
right_wheel_link
camera_link
camera_optical_frame
caster_link
```

### `footbot_gazebo`

Build type: `ament_cmake`

Purpose:

- owns Gazebo worlds
- stores ROS/Gazebo bridge reference config
- contains field, camera, ball, and soccer test scenes

Key files:

```text
footbot_gazebo/worlds/footbot_empty.sdf
footbot_gazebo/worlds/footbot_camera_test.sdf
footbot_gazebo/worlds/footbot_ball_follow.sdf
footbot_gazebo/worlds/footbot_opponent_detection.sdf
footbot_gazebo/worlds/footbot_soccer_field.sdf
footbot_gazebo/config/ros_gz_bridge.yaml
```

### `footbot_bringup`

Build type: `ament_cmake`

Purpose:

- owns launch files
- starts Gazebo
- starts robot state publishing
- starts ROS/Gazebo bridges
- starts control, perception, and debug workflows

Key launch files:

```text
spawn_footbot.launch.py
sim_gesture_control.launch.py
gesture_perception.launch.py
gesture_control.launch.py
ball_following.launch.py
opponent_detection.launch.py
soccer_field.launch.py
soccer_detection.launch.py
```

### `footbot_bridge`

Build type: `ament_python`

Purpose:

- exposes an ESP32-compatible HTTP `/move` endpoint
- translates legacy JSON movement commands into ROS 2 `Twist`
- keeps the old `manual_control/` client usable with the simulator

Key file:

```text
footbot_bridge/footbot_bridge/http_bridge.py
```

Default HTTP endpoint:

```text
http://127.0.0.1:8080/move
```

### `footbot_control`

Build type: `ament_python`

Purpose:

- converts high-level perception outputs into velocity commands
- owns gesture-to-velocity control
- owns ball-following control

Key files:

```text
footbot_control/footbot_control/gesture_to_cmd_vel_node.py
footbot_control/footbot_control/ball_follower_node.py
```

Output topic:

```text
/cmd_vel
```

### `footbot_perception`

Build type: `ament_python`

Purpose:

- owns generic perception utilities
- publishes webcam frames
- runs MediaPipe hand detection
- publishes gesture direction and speed
- detects the orange ball with OpenCV HSV segmentation
- provides debug image viewers

Key files:

```text
footbot_perception/footbot_perception/webcam_publisher_node.py
footbot_perception/footbot_perception/hand_detector_node.py
footbot_perception/footbot_perception/gesture_logic.py
footbot_perception/footbot_perception/debug_image_viewer_node.py
footbot_perception/footbot_perception/ball_detector_node.py
```

### `footbot_soccer_vision`

Build type: `ament_python`

Purpose:

- owns soccer-specific YOLO inference code
- runs opponent detection
- runs goal detection
- publishes annotated debug images
- captures images for future training datasets
- keeps runtime ROS code separate from `soccer_vision/` training notebooks

Key files:

```text
footbot_soccer_vision/footbot_soccer_vision/detectors/yolo_detector.py
footbot_soccer_vision/footbot_soccer_vision/nodes/opponent_detector_node.py
footbot_soccer_vision/footbot_soccer_vision/nodes/goal_detector_node.py
footbot_soccer_vision/footbot_soccer_vision/nodes/image_capture_node.py
footbot_soccer_vision/scripts/download_models.py
```

Model weights are ignored by Git:

```text
footbot_soccer_vision/models/weights/
```

### `footbot_soccer_msgs`

Build type: `ament_cmake`

Purpose:

- owns custom message interfaces for soccer behavior nodes
- currently provides `BallState`

Key file:

```text
footbot_soccer_msgs/msg/BallState.msg
```

### `footbot_soccer_behavior`

Build type: `ament_python`

Purpose:

- estimates ball-relative state from camera detections
- owns deterministic ball-control skills
- owns the ball-control finite state machine

Key files:

```text
footbot_soccer_behavior/footbot_soccer_behavior/ball_state_estimator_node.py
footbot_soccer_behavior/footbot_soccer_behavior/ball_control_fsm_node.py
footbot_soccer_behavior/footbot_soccer_behavior/skills/ball_control_skills.py
```

## ROS 2 Concepts Used

### Packages

Each folder under `simulation/ros2_ws/src/` is a ROS 2 package. Packages provide
source code, launch files, config, models, and metadata through `package.xml`.

### Build Types

Two build types are used:

- `ament_cmake`: good for asset/config/launch packages.
- `ament_python`: good for Python ROS nodes and command-line executables.

### Nodes

A node is a running ROS process. Examples:

```text
robot_state_publisher
joint_state_publisher
footbot_http_bridge
webcam_publisher
hand_detector
gesture_to_cmd_vel
ball_detector
ball_follower
opponent_detector
goal_detector
```

### Topics

Topics are named channels where messages are published and subscribed.

Important topics:

```text
/cmd_vel
/odom
/robot_description
/camera/image_raw
/camera/camera_info
/webcam/image_raw
/gesture/direction
/gesture/speed
/gesture/debug_image
/ball_detection
/ball/debug_image
/soccer/ball_state
/soccer/fsm_state
/opponent_detections
/opponent_detection/debug_image
/goal_detections
/goal_detection/debug_image
/soccer/camera/image_raw
/soccer/camera/camera_info
```

### Messages

Important message types:

```text
geometry_msgs/msg/Twist          velocity commands
nav_msgs/msg/Odometry            odometry
sensor_msgs/msg/Image            camera images
sensor_msgs/msg/CameraInfo       camera calibration/info
std_msgs/msg/String              gesture direction
std_msgs/msg/Float32             gesture speed
vision_msgs/msg/Detection2D      single 2D detection
vision_msgs/msg/Detection2DArray multiple 2D detections
footbot_soccer_msgs/msg/BallState estimated ball-control state
```

### Parameters

Nodes expose parameters for topic names, model paths, thresholds, gains, and
runtime options. Parameters are passed through `--ros-args -p` or launch files.

Example:

```bash
ros2 run footbot_soccer_vision opponent_detector \
  --ros-args -p image_topic:=/soccer/camera/image_raw
```

### Launch Files

Launch files start many nodes and processes together. The project uses Python
launch files in `footbot_bringup/launch/`.

Show launch arguments:

```bash
ros2 launch footbot_bringup soccer_detection.launch.py --show-args
```

## Gazebo Concepts Used

### SDF Worlds

Gazebo worlds are `.sdf` files under:

```text
simulation/ros2_ws/src/footbot_gazebo/worlds/
```

They define:

- ground planes
- lighting
- physics
- robots and objects
- goals and walls
- camera test objects
- ball and opponent scenes

Validate a world:

```bash
ign sdf -k simulation/ros2_ws/src/footbot_gazebo/worlds/footbot_soccer_field.sdf
```

### Xacro Robot Model

The main robot model is generated from Xacro:

```text
footbot_description/urdf/footbot.urdf.xacro
```

Xacro lets the model use properties and macros instead of repeated raw URDF.

Generate URDF manually:

```bash
ros2 run xacro xacro \
  simulation/ros2_ws/src/footbot_description/urdf/footbot.urdf.xacro \
  > /tmp/footbot.urdf
```

### Gazebo DiffDrive Plugin

The robot uses the Gazebo Fortress DiffDrive system plugin. ROS publishes
`geometry_msgs/msg/Twist` on `/cmd_vel`, `ros_gz_bridge` translates it to Gazebo
Transport, and Gazebo moves the robot.

### ROS/Gazebo Bridge

Gazebo Transport messages and ROS 2 messages are different. `ros_gz_bridge`
connects them.

Examples:

```text
/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist
/model/footbot/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry
/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image
/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo
```

Direction symbols:

```text
]  ROS to Gazebo
[  Gazebo to ROS
```

## Launch Workflows

Always build and source first:

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### Base Robot Simulation

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py
```

Headless:

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py use_gui:=false
```

What starts:

- Gazebo
- robot model spawn
- robot state publisher
- joint state publisher
- ROS/Gazebo bridge
- HTTP `/move` bridge by default

### Manual ROS Velocity Test

Forward:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.12, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

Rotate left:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.8}}"
```

Stop:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

### HTTP Compatibility Bridge

Launch:

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py
```

Status:

```bash
curl -s http://127.0.0.1:8080/status
```

Move:

```bash
curl -s -X POST http://127.0.0.1:8080/move \
  -H 'Content-Type: application/json' \
  -d '{"direction":"forward","speed":150}'
```

Stop:

```bash
curl -s -X POST http://127.0.0.1:8080/move \
  -H 'Content-Type: application/json' \
  -d '{"direction":"stop","speed":0}'
```

Legacy directions:

```text
forward
backward
left
right
soft_left
soft_right
stop
```

The bridge publishes zero Twist on shutdown and auto-stops stale commands after
a timeout.

### Simulated Robot Camera

Launch:

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py
```

Check topics:

```bash
ros2 topic list | grep camera
ros2 topic info /camera/image_raw
ros2 topic echo --once /camera/camera_info
```

View camera:

```bash
rqt_image_view /camera/image_raw
```

If `rqt_image_view` is missing:

```bash
sudo apt update
sudo apt install -y ros-humble-rqt-image-view
```

### ROS-Native Gesture Control

Full simulation with webcam gesture control:

```bash
ros2 launch footbot_bringup sim_gesture_control.launch.py
```

With debug hand-landmark window:

```bash
ros2 launch footbot_bringup sim_gesture_control.launch.py show_debug_view:=true
```

Only webcam and gesture perception:

```bash
ros2 launch footbot_bringup gesture_perception.launch.py
```

Only gesture-to-velocity:

```bash
ros2 launch footbot_bringup gesture_control.launch.py
```

Check topics:

```bash
ros2 topic list | grep -E 'webcam|gesture|cmd_vel'
ros2 topic echo /gesture/direction
ros2 topic echo /gesture/speed
```

### Autonomous Ball Following

Launch:

```bash
ros2 launch footbot_bringup ball_following.launch.py
```

With debug view:

```bash
ros2 launch footbot_bringup ball_following.launch.py show_debug_view:=true
```

Topics:

```text
/camera/image_raw
/ball_detection
/ball/debug_image
/cmd_vel
```

The detector uses HSV color segmentation for an orange ball. It is not YOLO.
The controller uses proportional control:

- rotate toward off-center ball
- move forward when centered
- stop when close
- stop when detection is stale

### Soccer Ball Control

Launch deterministic ball control:

```bash
ros2 launch footbot_bringup ball_control.launch.py
```

Launch a specific scenario:

```bash
ros2 launch footbot_bringup ball_control.launch.py scenario:=misaligned show_debug_view:=true
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

Topics:

```text
/ball_detection
/ball/debug_image
/soccer/ball_state
/soccer/fsm_state
/cmd_vel
```

Finite-state machine states:

```text
SEARCH_BALL
ALIGN_TO_BALL
APPROACH_BALL
CONTACT_BALL
CONTROL_BALL
ROTATE_WITH_BALL
RECOVER_BALL
STOP_SAFE
```

The behavior uses the existing HSV ball detector, then estimates `BallState`,
then uses an FSM to select deterministic skills. It is not full dribbling,
shooting, opponent interaction, or team play.

Multi-lane stress test:

```bash
ros2 launch footbot_bringup ball_control_multi.launch.py
```

This launch starts three robots and three dynamic balls in the same Gazebo
simulation. Divider walls isolate the lanes so each robot sees only its own
ball. The lanes are:

```text
front   ball starts centered in front of the robot
far     ball starts farther away in front of the robot
behind  ball starts behind the robot, so search rotation is required
```

Topic trees are isolated per lane:

```text
/ball_control/front/camera/image_raw
/ball_control/front/ball_detection
/ball_control/front/soccer/ball_state
/ball_control/front/soccer/fsm_state
/ball_control/front/cmd_vel
```

### YOLO Opponent Detection

Install YOLO runtime dependencies:

```bash
python3 -m pip install --user -r simulation/requirements-yolo.txt
```

Launch opponent detector test scene:

```bash
ros2 launch footbot_bringup opponent_detection.launch.py show_debug_view:=true
```

Topics:

```text
/camera/image_raw
/opponent_detections
/opponent_detection/debug_image
```

The default model is `yolo11n.pt`. It can validate the ROS/YOLO pipeline, but a
custom trained model is required for reliable FootBot-opponent detection.

### Soccer Field Scene

Launch field only:

```bash
ros2 launch footbot_bringup soccer_field.launch.py
```

What appears:

- green field
- border walls
- two goals
- center ball
- three blue FootBot-like robots
- three red FootBot-like robots
- mirrored triangular team positions

The field launch also bridges a camera mounted on the blue goalkeeper:

```text
/soccer/camera/image_raw
/soccer/camera/camera_info
```

Check the field camera:

```bash
ros2 topic list | grep /soccer/camera
ros2 topic hz /soccer/camera/image_raw
```

### Soccer Goal And Opponent Detection

Launch field plus YOLO detectors:

```bash
ros2 launch footbot_bringup soccer_detection.launch.py show_debug_view:=true
```

Topics:

```text
/soccer/camera/image_raw
/soccer/camera/camera_info
/opponent_detections
/opponent_detection/debug_image
/goal_detections
/goal_detection/debug_image
```

Use a trained model:

```bash
ros2 launch footbot_bringup soccer_detection.launch.py \
  show_debug_view:=true \
  model_path:=/media/josedanielchg/Data/Proyectos/Robotica/footbot/soccer_vision/models/yolo11s/soccer_yolo.pt \
  opponent_classes:=opponent \
  goal_classes:=goal
```

The detector can use the existing `soccer_vision/models/yolo11s/soccer_yolo.pt`
model. That model is outside the ROS workspace and is treated as a training
artifact/reference model.

## Training And Labeling Workflow

Use the existing top-level `soccer_vision/` folder for labeling, datasets,
notebooks, and training:

```text
soccer_vision/
```

That folder already contains:

```text
soccer_vision/.venv/
soccer_vision/requirements.txt
soccer_vision/data.yaml
soccer_vision/dataset/
soccer_vision/notebooks/
soccer_vision/models/yolo11s/soccer_yolo.pt
```

Existing classes:

```text
goal
opponent
```

Use this split:

- `soccer_vision/`: label, train, evaluate, export model weights.
- `simulation/ros2_ws/src/footbot_soccer_vision/`: load weights and publish ROS detections.

Do not train inside the ROS 2 package.

Activate the existing training environment if it works on the current OS:

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/soccer_vision
source .venv/bin/activate
```

If `.venv` was created on Windows and does not activate on Ubuntu, create a
Linux environment:

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/soccer_vision
python3 -m venv .venv_linux
source .venv_linux/bin/activate
pip install -r requirements.txt
```

Run Label Studio:

```bash
label-studio
```

Train with Ultralytics:

```bash
yolo detect train \
  model=yolo11s.pt \
  data=soccer_vision/data.yaml \
  epochs=60 \
  imgsz=640 \
  batch=16
```

Use the trained model in ROS by passing `model_path`.

If a model should be copied into the ROS package locally, place it under:

```text
simulation/ros2_ws/src/footbot_soccer_vision/models/weights/
```

Model files such as `.pt` and `.onnx` are ignored by Git. Use Git LFS later if
the project needs to version model weights.

## Dataset Capture From Simulation

Capture images from the default robot camera:

```bash
ros2 run footbot_soccer_vision image_capture \
  --ros-args -p image_topic:=/camera/image_raw
```

Capture images from the soccer field camera:

```bash
ros2 run footbot_soccer_vision image_capture \
  --ros-args -p image_topic:=/soccer/camera/image_raw -p session_name:=soccer_field_v1
```

Dataset layout used by `footbot_soccer_vision`:

```text
datasets/raw/<session>/images/*.jpg
datasets/raw/<session>/metadata.csv
datasets/labels/<session>/*.txt
datasets/splits/data.yaml
```

Generated dataset files should remain uncommitted by default.

## Control Ownership Rule

Only one node should own `/cmd_vel` at a time.

Do not run these control modes together:

- HTTP bridge/manual control
- ROS-native gesture control
- ball follower
- future autonomous soccer behavior

Opponent and goal detection are perception-only and should not publish
`/cmd_vel`.

## Verification Commands

Build:

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Check launch arguments:

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py --show-args
ros2 launch footbot_bringup ball_following.launch.py --show-args
ros2 launch footbot_bringup soccer_detection.launch.py --show-args
```

Check package executables:

```bash
ros2 pkg executables footbot_bridge
ros2 pkg executables footbot_perception
ros2 pkg executables footbot_control
ros2 pkg executables footbot_soccer_vision
```

Check important topics:

```bash
ros2 topic list | sort
ros2 topic info /cmd_vel
ros2 topic info /camera/image_raw
ros2 topic info /opponent_detections
ros2 topic info /goal_detections
```

Check TF frames:

```bash
ros2 run tf2_tools view_frames
```

Check Gazebo transport topics:

```bash
ign topic -l
```

Validate SDF worlds:

```bash
ign sdf -k simulation/ros2_ws/src/footbot_gazebo/worlds/footbot_soccer_field.sdf
```

## Common Problems

### `ros2` Command Not Found

Source ROS 2:

```bash
source /opt/ros/humble/setup.bash
```

### Package Not Found

Build and source the workspace:

```bash
cd simulation/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

### Camera Topic Missing

Make sure the relevant launch file starts the camera bridge:

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py
ros2 launch footbot_bringup soccer_field.launch.py
```

Then check:

```bash
ros2 topic list | grep camera
```

### YOLO Import Error

Install:

```bash
python3 -m pip install --user -r simulation/requirements-yolo.txt
```

### NumPy ABI Error

Force NumPy 1.x:

```bash
python3 -m pip install --user --force-reinstall "numpy==1.26.4"
```

### Robot Does Not Move

Check:

```bash
ros2 topic info /cmd_vel
ros2 topic echo /cmd_vel
ros2 topic echo /odom
```

Make sure only one controller publishes `/cmd_vel`.

### Debug Image Is Black

Check that the source image publishes:

```bash
ros2 topic hz /camera/image_raw
ros2 topic hz /soccer/camera/image_raw
```

If the camera image exists but detections are empty, the model may not recognize
the current objects.

## Current Limitations

- Soccer field robots are static visual/collision placeholders.
- Multi-robot control is not implemented yet.
- YOLO goal/opponent reliability depends on trained weights.
- Ball following uses HSV segmentation, not YOLO.
- The HTTP bridge is for compatibility, not final architecture.
- Existing `manual_control/`, `esp32cam_robot/`, and `auto_soccer_bot/` remain unchanged.
- Model weights and generated datasets are not committed by default.

## Suggested Future Work

- Convert field players into individually spawned controllable robots.
- Add namespaces for multi-robot topics.
- Train a simulation-specific YOLO model for `goal`, `opponent`, and `ball`.
- Add team-aware soccer behavior nodes.
- Add behavior arbitration so manual, gesture, ball follower, and soccer modes cannot conflict.
- Add ROS bags and repeatable validation scenarios.
- Decide whether model weights should be tracked with Git LFS.
