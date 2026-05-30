# Verification

Run these checks after installing the simulation stack.

## ROS 2 CLI

```bash
source /opt/ros/humble/setup.bash
ros2 --version
ros2 doctor
ros2 pkg list | grep demo_nodes
```

Expected result:

- `ros2` is available.
- `ros2 doctor` runs without blocking errors.
- Demo packages are visible.

## ROS 2 Talker/Listener

Terminal 1:

```bash
source /opt/ros/humble/setup.bash
ros2 run demo_nodes_cpp talker
```

Terminal 2:

```bash
source /opt/ros/humble/setup.bash
ros2 run demo_nodes_py listener
```

Expected result:

- The talker prints publishing messages.
- The listener prints received messages.

## Gazebo Fortress

```bash
ign gazebo --versions
ign gazebo
```

Expected result:

- Gazebo reports Fortress/Ignition Gazebo versions.
- The Gazebo GUI opens.

For Fortress, prefer `ign gazebo`. The newer `gz sim` command is used by later Gazebo releases such as Harmonic.

## ROS/Gazebo Packages

```bash
source /opt/ros/humble/setup.bash
ros2 pkg list | grep ros_gz
```

Expected result:

- Packages such as `ros_gz_bridge`, `ros_gz_sim`, or related `ros_gz` packages are listed.

## Optional Workspace Sanity Check

The workspace source directory should exist:

```bash
test -d simulation/ros2_ws/src
```

## FootBot Movement Simulation

Build and source the workspace:

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot
source /opt/ros/humble/setup.bash
cd simulation/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

Launch the simulation:

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py
```

For a headless server-only check:

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py use_gui:=false
```

In another terminal, check movement topics:

```bash
source /opt/ros/humble/setup.bash
source /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws/install/setup.bash

ros2 topic list | sort
ros2 topic info /cmd_vel
ros2 topic echo --once /odom
```

Send test commands:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.12, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"

ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: -0.12, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"

ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.8}}"

ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: -0.8}}"

ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

Expected result:

- `/cmd_vel` exists as `geometry_msgs/msg/Twist`.
- `/odom` publishes `nav_msgs/msg/Odometry`.
- Positive `linear.x` moves the robot forward.
- Negative `linear.x` moves the robot backward.
- Positive `angular.z` rotates left.
- Negative `angular.z` rotates right.
- Zero Twist stops the robot.

If odometry is missing, inspect the underlying Gazebo topic:

```bash
ign topic -l | grep -E 'cmd_vel|odom|odometry'
```

The current bridge maps Gazebo `/model/footbot/odometry` to ROS `/odom`.

## HTTP Command Bridge

Launch the simulation with the HTTP bridge enabled:

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch footbot_bringup spawn_footbot.launch.py
```

For a headless check:

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py use_gui:=false
```

Check bridge status:

```bash
curl -s http://127.0.0.1:8080/status
```

Send HTTP movement commands:

```bash
curl -s -X POST http://127.0.0.1:8080/move \
  -H 'Content-Type: application/json' \
  -d '{"direction":"forward","speed":150}'

curl -s -X POST http://127.0.0.1:8080/move \
  -H 'Content-Type: application/json' \
  -d '{"direction":"backward","speed":150}'

curl -s -X POST http://127.0.0.1:8080/move \
  -H 'Content-Type: application/json' \
  -d '{"direction":"left","speed":150}'

curl -s -X POST http://127.0.0.1:8080/move \
  -H 'Content-Type: application/json' \
  -d '{"direction":"right","speed":150}'

curl -s -X POST http://127.0.0.1:8080/move \
  -H 'Content-Type: application/json' \
  -d '{"direction":"soft_left","speed":180,"turn_ratio":0.4}'

curl -s -X POST http://127.0.0.1:8080/move \
  -H 'Content-Type: application/json' \
  -d '{"direction":"soft_right","speed":180,"turn_ratio":0.4}'

curl -s -X POST http://127.0.0.1:8080/move \
  -H 'Content-Type: application/json' \
  -d '{"direction":"stop","speed":0}'
```

Check invalid command handling:

```bash
curl -i -X POST http://127.0.0.1:8080/move \
  -H 'Content-Type: application/json' \
  -d '{"direction":"fly","speed":150}'
```

Expected result:

- Valid HTTP commands return `200`.
- Invalid movement directions return `400`.
- `/cmd_vel` receives `geometry_msgs/msg/Twist`.
- The robot moves in Gazebo for movement commands.
- The robot stops after `stop` or after the command timeout.

Inspect the ROS output:

```bash
ros2 topic echo /cmd_vel
ros2 topic info /cmd_vel
ros2 topic echo /odom
```

## Robot Camera

The simulation includes a camera sensor mounted on `camera_link`. Camera data is
bridged from Gazebo to ROS 2:

```text
/camera/image_raw
/camera/camera_info
```

Launch the simulation:

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch footbot_bringup spawn_footbot.launch.py
```

Check camera topics:

```bash
ros2 topic list | grep camera
ros2 topic info /camera/image_raw
ros2 topic info /camera/camera_info
ros2 topic hz /camera/image_raw
ros2 topic echo --once /camera/camera_info
```

Expected result:

- `/camera/image_raw` is `sensor_msgs/msg/Image`.
- `/camera/camera_info` is `sensor_msgs/msg/CameraInfo`.
- Image dimensions are `640x480`.
- `camera_info.header.frame_id` is `camera_optical_frame`.
- Image publishing is near `15 Hz`.

View the camera stream:

```bash
rqt_image_view /camera/image_raw
```

The default Gazebo world includes colored objects in front of the robot so the
camera view is easy to recognize.

Check camera frames:

```bash
ros2 run tf2_tools view_frames
ros2 run tf2_ros tf2_echo base_link camera_link
ros2 run tf2_ros tf2_echo camera_link camera_optical_frame
```

Expected result:

- `camera_link` is attached to `base_link`.
- `camera_optical_frame` is attached to `camera_link`.
- The camera topics keep publishing while the robot moves.

## ROS-Native Gesture Control

Install the MediaPipe/NumPy versions used by the gesture detector:

```bash
python3 -m pip install --user --force-reinstall "numpy==1.26.4" "mediapipe==0.10.14"
```

Build and source the workspace:

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Check executables:

```bash
ros2 pkg executables footbot_perception
ros2 pkg executables footbot_control
```

Expected result:

- `footbot_perception webcam_publisher`
- `footbot_perception hand_detector`
- `footbot_perception debug_image_viewer`
- `footbot_control gesture_to_cmd_vel`

Test gesture-to-velocity control without a webcam:

```bash
ros2 run footbot_control gesture_to_cmd_vel
```

In another terminal:

```bash
ros2 topic echo /cmd_vel
```

Publish fake gesture messages:

```bash
ros2 topic pub --once /gesture/speed std_msgs/msg/Float32 "{data: 0.6}"
ros2 topic pub --once /gesture/direction std_msgs/msg/String "{data: forward}"
```

Expected result:

- `/cmd_vel.linear.x` becomes positive.
- `/cmd_vel` returns to zero after the command timeout.

Test the webcam publisher:

```bash
ros2 run footbot_perception webcam_publisher --ros-args -p camera_index:=0
ros2 topic info /webcam/image_raw
ros2 topic hz /webcam/image_raw
```

Test hand detection:

```bash
ros2 run footbot_perception hand_detector
ros2 topic echo /gesture/direction
ros2 topic echo /gesture/speed
ros2 run footbot_perception debug_image_viewer
```

Launch the full simulation with ROS-native gesture control:

```bash
ros2 launch footbot_bringup sim_gesture_control.launch.py
```

Launch with a local MediaPipe-style debug window:

```bash
ros2 launch footbot_bringup sim_gesture_control.launch.py show_debug_view:=true
```

Expected result:

- Gazebo starts.
- The HTTP `/move` bridge remains available.
- Webcam gesture topics are published.
- A debug window can show hand landmarks, speed, and direction.
- Gesture commands publish `/cmd_vel`.
- The robot moves from gestures.
- Gazebo camera topics still publish.

## Autonomous Ball Following

Build and source the workspace:

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Check executables:

```bash
ros2 pkg executables footbot_perception | grep ball_detector
ros2 pkg executables footbot_control | grep ball_follower
```

Launch the autonomous mode:

```bash
ros2 launch footbot_bringup ball_following.launch.py
```

Launch with a detector debug window:

```bash
ros2 launch footbot_bringup ball_following.launch.py show_debug_view:=true
```

Inspect topics:

```bash
ros2 topic list | grep -E 'camera|ball|cmd_vel|odom'
ros2 topic info /ball_detection
ros2 topic echo /ball_detection
ros2 topic echo /cmd_vel
```

Expected result:

- `/ball_detection` publishes `vision_msgs/msg/Detection2D` when the orange ball is visible.
- `/ball/debug_image` shows the ball detection overlay.
- The robot rotates toward off-center ball positions.
- The robot drives toward a centered ball.
- The robot stops when the ball is close or no longer visible.

Test the ball follower without the detector:

```bash
ros2 run footbot_control ball_follower
ros2 topic echo /cmd_vel
```

Publish a centered fake detection:

```bash
ros2 topic pub --once /ball_detection vision_msgs/msg/Detection2D \
"{header: {frame_id: camera_optical_frame}, bbox: {center: {position: {x: 320.0, y: 240.0}, theta: 0.0}, size_x: 40.0, size_y: 40.0}, results: [{hypothesis: {class_id: ball, score: 0.9}}]}"
```

Expected result:

- Centered/far detections publish positive `linear.x`.
- Left detections publish positive `angular.z`.
- Right detections publish negative `angular.z`.
- Close or stale detections publish zero Twist.
