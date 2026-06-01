# footbot_bringup

Launch and orchestration package for the Footbot simulation.

Current contents:

- Launch files for Gazebo
- Launch files for robot description
- Launch setup for ROS/Gazebo movement topic bridge
- Launch setup for ROS/Gazebo camera topic bridge
- Launch setup for the ESP32-compatible HTTP command bridge
- Launch setup for ROS-native webcam gesture perception
- Launch setup for ROS-native gesture-to-velocity control
- Launch setup for autonomous ball following
- Launch setup for deterministic soccer ball control
- Launch setup for YOLO opponent detection
- Launch setup for the soccer field layout scene
- Optional server-only launch mode for headless checks

Gesture-control launch files:

```bash
ros2 launch footbot_bringup gesture_perception.launch.py
ros2 launch footbot_bringup gesture_control.launch.py
ros2 launch footbot_bringup sim_gesture_control.launch.py
```

Open the gesture debug image window with:

```bash
ros2 launch footbot_bringup sim_gesture_control.launch.py show_debug_view:=true
```

Autonomous ball-following launch:

```bash
ros2 launch footbot_bringup ball_following.launch.py
ros2 launch footbot_bringup ball_following.launch.py show_debug_view:=true
```

The autonomous launch disables the HTTP command bridge by default so `ball_follower` owns `/cmd_vel`.

Soccer ball-control launch:

```bash
ros2 launch footbot_bringup ball_control.launch.py
ros2 launch footbot_bringup ball_control.launch.py scenario:=misaligned show_debug_view:=true
```

This mode starts the ball-control world, spawns one robot and one dynamic ball,
starts HSV ball detection, estimates `/soccer/ball_state`, and runs the
ball-control FSM as the only `/cmd_vel` owner.

Multi-lane soccer ball-control launch:

```bash
ros2 launch footbot_bringup ball_control_multi.launch.py
ros2 launch footbot_bringup ball_control_multi.launch.py show_debug_view:=true
```

This mode starts three isolated wall-separated lanes in one Gazebo world. Each
lane has its own robot, ball, camera topic, detector, estimator, FSM, and
command topic under `/ball_control/<lane>/`. The lanes cover a normal front
ball, a farther ball, and a ball that starts behind the robot.

YOLO opponent-detection launch:

```bash
ros2 launch footbot_bringup opponent_detection.launch.py
ros2 launch footbot_bringup opponent_detection.launch.py show_debug_view:=true
```

This mode starts the opponent test world and perception nodes only. It does not
start HTTP control, gesture control, or ball following.

Soccer field scene:

```bash
ros2 launch footbot_bringup soccer_field.launch.py
```

This opens the field, goals, walls, center ball, and two static three-robot
teams. It does not spawn a controlled robot or start control nodes.

Soccer field detection:

```bash
ros2 launch footbot_bringup soccer_detection.launch.py
ros2 launch footbot_bringup soccer_detection.launch.py show_debug_view:=true
```

This opens the soccer field, bridges the blue goalkeeper camera, and starts
YOLO-based goal and opponent detector nodes. Pass custom weights with:

```bash
ros2 launch footbot_bringup soccer_detection.launch.py model_path:=/path/to/best.pt
```

Future contents:

- Shared runtime configuration

Not implemented yet:

- Navigation startup
