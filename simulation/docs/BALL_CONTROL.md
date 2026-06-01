# Ball Control

Ball control is the only currently implemented autonomous soccer behavior. It
uses deterministic perception, state estimation, skills, and an FSM.

## Launch

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
