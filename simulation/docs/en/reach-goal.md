# Reach Goal With Ball

Reach Goal is the production autonomous behavior for driving the ball into a
visible goal. One FootBot uses
its robot-mounted camera, a YOLO `ball`+`goal` detector, an image-derived state
estimator, bounded skills, and a finite-state machine to push the ball toward a
visible goal. Every control decision is perception-driven; the behavior never
reads Gazebo ground-truth poses.

## Launch

Build and source first:

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Run the Reach-goal behavior with the trained model:

```bash
ros2 launch footbot_bringup reach_goal.launch.py \
  model_path:=/media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws/src/footbot_soccer_vision/models/reach_goal_ball_goal/reach_goal_ball_goal_v1_best.pt \
  show_debug_view:=true \
  run_behavior:=true
```

The launch starts the reach-goal Gazebo world, spawns the FootBot, spawns the ball,
runs the YOLO detector, opens the optional debug viewer, and starts the reach-goal
ball+goal state estimator, the simulation score monitor, and the reach-goal
FSM. It does **not** start the HTTP bridge, gesture controller, simple ball
follower, or the Ball Control FSM.

Set `run_behavior:=false` to inspect perception only (no robot motion).

## Launch Arguments

```text
model_path              absolute path to the trained ball+goal weights
run_behavior            start the estimator + FSM (default true)
run_score_monitor       start the simulation scoring referee (default true)
show_debug_view         open the YOLO debug image window (default true)
confidence_threshold    YOLO score threshold (default 0.25; lower to debug)
detections_topic        /soccer/detections
ball_goal_state_topic   /soccer/ball_goal_state
fsm_state_topic         /soccer/reach_goal_fsm_state
goal_scored_topic       /soccer/goal_scored
ball_pose_topic         /reach_goal/ball_pose
world_pose_topic        /world/footbot_world/pose/info
ball_entity_name        reach_goal_ball
cmd_vel_topic           /cmd_vel
camera_topic            /camera/image_raw
```

## Topics

```text
/camera/image_raw          robot camera (input)
/soccer/detections         YOLO ball+goal Detection2DArray
/soccer/detections/debug_image
/soccer/ball_goal_state    footbot_soccer_msgs/BallGoalState (image-derived)
/soccer/reach_goal_fsm_state   std_msgs/String current FSM state
/soccer/goal_scored        std_msgs/Bool simulation referee score signal
/world/footbot_world/pose/info
                          tf2_msgs/TFMessage Gazebo world pose stream
/reach_goal/ball_pose          optional geometry_msgs/Pose direct ball-pose input
/cmd_vel                   geometry_msgs/Twist (FSM only)
```

Inspect them while the behavior runs:

```bash
ros2 topic echo /soccer/detections
ros2 topic echo /soccer/ball_goal_state
ros2 topic echo /soccer/reach_goal_fsm_state
ros2 topic echo /soccer/goal_scored
ros2 topic echo /cmd_vel
```

## Nodes

| Node | Package | Purpose |
| --- | --- | --- |
| `yolo_detector` | `footbot_soccer_vision` | YOLO `ball`+`goal` detection from `/camera/image_raw`. |
| `ball_goal_state_estimator` | `footbot_soccer_behavior` | Converts `Detection2DArray` into `BallGoalState`. |
| `reach_goal_fsm` | `footbot_soccer_behavior` | Chooses skills and publishes `/cmd_vel`. |
| `reach_goal_score_monitor` | `footbot_soccer_behavior` | Simulation referee that stops the episode after a scored goal. |

## State Message

`footbot_soccer_msgs/msg/BallGoalState` is image-derived only:

```text
bool  ball_visible / goal_visible / stale
float ball_confidence / goal_confidence
float ball_center_error / goal_center_error   normalized horizontal error
float ball_angle_rad / goal_angle_rad         bearing from optical axis
float ball_radius_px                          apparent ball size (range proxy)
float goal_width_px                           apparent goal size
bool  has_ball_control                        conservative: close + centered
bool  ball_goal_aligned                       ball and goal share a bearing
bool  goal_memory_active                      last goal bearing is being reused
float goal_memory_age_sec                     age of the remembered goal
```

`stale` means the detection pipeline stopped delivering frames. `ball_visible`
and `goal_visible` mean each object appeared in a recent frame.

The goal can disappear from the camera when the robot gets close to the open
mouth of the goal. The estimator keeps a short temporal memory of the last
valid goal bearing while the ball remains controlled, so the FSM can finish
the dribble instead of falling back to `SEARCH_GOAL` because of one temporary
YOLO dropout.

## FSM States

```text
SEARCH_BALL          no ball in view, rotate to scan
APPROACH_BALL        ball visible, drive toward it (slows as it grows)
CONTROL_BALL         ball in frontal control zone, keep it centered
SEARCH_GOAL          ball controlled, goal unseen, rotate while holding ball
ALIGN_BALL_TO_GOAL   ball+goal visible but off-bearing, turn gently with ball
DRIBBLE_TO_GOAL      ball lined up with goal, drive forward
RECOVER_BALL         lost control, back off and re-acquire the ball
STOP_SAFE            stale perception or emergency stop, zero velocity
GOAL_SCORED          simulation referee detected score, zero velocity forever
```

The FSM owns transitions; skills only produce bounded `Twist` commands. Losing
`has_ball_control` from any holding state drops to `RECOVER_BALL`. Stale
perception forces `STOP_SAFE`, and the behavior resumes searching once fresh
detections return. The FSM publishes a zero `Twist` on shutdown.

When `/soccer/goal_scored` becomes true, the FSM transitions to `GOAL_SCORED`
and keeps publishing zero velocity until the launch/session is restarted.

## Shared Defaults

Estimator and FSM defaults are documented in:

```text
simulation/ros2_ws/src/footbot_soccer_behavior/config/reach_goal.yaml
```

The estimator uses the camera width (`640`) and horizontal FOV (`1.047` rad) to
turn bbox centers into bearings, and apparent ball radius as a rough range proxy.
This is simulation-appropriate, not a calibrated 3D estimator.

## `/cmd_vel` Ownership

Only `reach_goal_fsm` publishes `/cmd_vel` in reach-goal mode. Do not run
another `/cmd_vel` owner (HTTP bridge, gesture control, ball follower, or the
Ball Control FSM) at the same time, or the commands will fight.

## Goal Detection Troubleshooting

The behavior depends on the YOLO model detecting the `goal`. The ball is usually
easy; the goal is harder.

1. Lower the threshold to confirm the goal is detectable at all:

   ```bash
   ros2 launch footbot_bringup reach_goal.launch.py \
     model_path:=/absolute/path/to/reach_goal_ball_goal_v1_best.pt \
     confidence_threshold:=0.05 \
     show_debug_view:=true
   ```

2. Inspect detections and rate:

   ```bash
   ros2 topic echo /soccer/detections
   ros2 topic hz /soccer/detections
   ```

3. If the goal still does not appear, improve the dataset/model (do **not**
   hardcode the goal pose or use Gazebo ground truth):
   - Capture camera images from the reach-goal scene with `image_capture`.
   - Label more `goal` examples in Label Studio.
   - Re-run `prepare_reach_goal_dataset.py`, validate, and retrain. See
     [perception-and-datasets.md](perception-and-datasets.md).

Optionally adjust the simulated goal visual in
`footbot_gazebo/worlds/footbot_reach_goal.sdf` so it better matches the
training images, but keep it visible to the robot camera and distinct from the
ball.

## Score Detection

Scoring uses simulation referee logic, not robot perception. The launch bridges
Gazebo's world pose stream from `/world/footbot_world/pose/info`, and
`reach_goal_score_monitor` extracts the `reach_goal_ball` pose from that message. It can
also consume `/reach_goal/ball_pose` if a direct model-pose bridge is available in a
future Gazebo setup. The monitor publishes `/soccer/goal_scored` once the ball
remains inside the goal zone long enough:

```text
ball_x >= 1.68
abs(ball_y) <= 0.38
ball_z <= 0.20
hold time >= 0.15 s
```

This lets the reach-goal behavior stop cleanly after a goal without giving the robot any
ground-truth information for navigation.

## Current Limits

This behavior drives one robot to push the ball toward a goal and stops the
episode when the simulation referee detects a score. It does not steal from
opponents, coordinate a team, or use reinforcement learning.
