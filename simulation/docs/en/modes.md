# Simulation Modes

Build and source before launching any mode:

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## Base Manual Mode

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py
```

Starts Gazebo, spawns the robot, bridges `/cmd_vel`, `/odom`, and camera topics,
and starts the HTTP bridge by default.

HTTP command example:

```bash
curl -s -X POST http://127.0.0.1:8080/move \
  -H 'Content-Type: application/json' \
  -d '{"direction":"forward","speed":150}'
```

## ROS-Native Gesture Mode

```bash
ros2 launch footbot_bringup sim_gesture_control.launch.py show_debug_view:=true
```

Uses the computer webcam, MediaPipe hand detection, gesture topics, and
`gesture_to_cmd_vel`.

## Simple Ball Follower

```bash
ros2 launch footbot_bringup ball_following.launch.py show_debug_view:=true
```

This is a simple HSV detector plus proportional ball follower. It is useful as
a perception/control smoke test, but it is not the main soccer behavior.

## Deterministic Ball Control

```bash
ros2 launch footbot_bringup ball_control.launch.py scenario:=front show_debug_view:=true
```

This is the foundational autonomous soccer behavior for ball possession. See
[ball-control.md](ball-control.md).

## Multi-Lane Ball Control Test

```bash
ros2 launch footbot_bringup ball_control_multi.launch.py show_debug_view:=true
```

Runs isolated front, far, and behind-ball scenarios in one world with separate
namespaced topics.

## Reach Goal With Ball

```bash
ros2 launch footbot_bringup reach_goal.launch.py \
  model_path:=/media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws/src/footbot_soccer_vision/models/reach_goal_ball_goal/reach_goal_ball_goal_v1_best.pt \
  show_debug_view:=true \
  run_behavior:=true
```

Starts one controllable FootBot, one dynamic ball in front of it, one goal
farther ahead, the robot camera bridge on `/camera/image_raw`, the Reach Goal YOLO
detector on `/soccer/detections`, the ball+goal state estimator, the simulation
score monitor on `/soccer/goal_scored`, and the reach-goal FSM that pushes the
ball toward the goal.

Only the Reach Goal FSM owns `/cmd_vel` in this mode. Pass `run_behavior:=false` to
inspect perception only. Pass `run_score_monitor:=false` only when debugging the
referee separately. See [reach-goal.md](reach-goal.md).

## Perception-Only Soccer Modes

```bash
ros2 launch footbot_bringup opponent_detection.launch.py show_debug_view:=true
ros2 launch footbot_bringup soccer_detection.launch.py show_debug_view:=true
```

These modes observe camera images and publish detections/debug images. They do
not own `/cmd_vel`.

`soccer_detection.launch.py` uses the soccer-field camera topic
`/soccer/camera/image_raw`. The Reach-goal scene uses the robot-mounted
camera topic `/camera/image_raw`.

## Soccer Field Visualization

```bash
ros2 launch footbot_bringup soccer_field.launch.py
```

Opens the field with walls, goals, a center ball, and mirrored static teams.
