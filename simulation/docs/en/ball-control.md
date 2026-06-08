# Ball Control

Ball control is the only currently implemented autonomous soccer behavior. It
uses deterministic perception, state estimation, skills, and an FSM.

<p align="center">
  <img src="src/ball-control-debug.png" alt="Ball-control debug screenshot" />
</p>

**Figure 1.** Ball Control running in Gazebo with the debug image viewer showing
the detected orange ball and state feedback.

## Launch

Build and source first:

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Run the single-scenario ball-control behavior:

```bash
ros2 launch footbot_bringup ball_control.launch.py scenario:=front show_debug_view:=true
```

Scenarios:

```text
front
left
right
far
close
misaligned
```

## Multi-Lane Test

The multi-lane launch starts three wall-separated scenarios in one Gazebo world:

```text
front   ball starts in front of the robot
far     ball starts farther away
behind  ball starts behind the robot, so the robot must rotate to search
```

Launch without debug windows:

```bash
ros2 launch footbot_bringup ball_control_multi.launch.py
```

Launch with debug image windows:

```bash
ros2 launch footbot_bringup ball_control_multi.launch.py show_debug_view:=true
```

In another terminal, source the workspace:

```bash
source /opt/ros/humble/setup.bash
source /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws/install/setup.bash
```

List the lane-specific topics:

```bash
ros2 topic list | grep ball_control
```

Inspect FSM state for each lane:

```bash
ros2 topic echo /ball_control/front/soccer/fsm_state
ros2 topic echo /ball_control/far/soccer/fsm_state
ros2 topic echo /ball_control/behind/soccer/fsm_state
```

Inspect estimated ball state:

```bash
ros2 topic echo /ball_control/front/soccer/ball_state
ros2 topic echo /ball_control/far/soccer/ball_state
ros2 topic echo /ball_control/behind/soccer/ball_state
```

Inspect velocity commands:

```bash
ros2 topic echo /ball_control/front/cmd_vel
ros2 topic echo /ball_control/far/cmd_vel
ros2 topic echo /ball_control/behind/cmd_vel
```

Expected behavior:

- `front`: detects the ball quickly and approaches it.
- `far`: approaches more slowly because the ball starts farther away.
- `behind`: rotates to search before it can align with the ball.
- Each lane uses isolated topics under `/ball_control/<lane>/`.

## Topics

```text
/camera/image_raw
/ball_detection
/ball/debug_image
/soccer/ball_state
/soccer/fsm_state
/cmd_vel
```

## Nodes

| Node | Package | Purpose |
| --- | --- | --- |
| `ball_detector` | `footbot_perception` | HSV orange-ball detection from the robot camera. |
| `ball_state_estimator` | `footbot_soccer_behavior` | Converts `Detection2D` into `BallState`. |
| `ball_control_fsm` | `footbot_soccer_behavior` | Chooses skills and publishes `/cmd_vel`. |

## FSM States

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

The FSM owns transitions. Skills only produce bounded `Twist` commands for the
current state.

## Shared Defaults

Default parameters are documented in:

```text
simulation/ros2_ws/src/footbot_soccer_behavior/config/ball_control.yaml
```

The estimator uses apparent ball radius and camera FOV to estimate rough range.
This is simulation-appropriate but not a calibrated 3D pose estimator.

## Current Limits

This behavior does not shoot, score goals, steal from opponents, coordinate a
team, or use reinforcement learning.
