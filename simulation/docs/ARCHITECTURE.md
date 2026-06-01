# Architecture

The simulation is isolated under `simulation/` and should not require changes to
`esp32cam_robot/` or `manual_control/`.

## Main Data Flow

```text
Gazebo world
  -> robot model from footbot_description
  -> camera and odometry Gazebo Transport topics
  -> ros_gz_bridge
  -> ROS topics
```

Movement uses:

```text
/cmd_vel -> ros_gz_bridge -> Gazebo DiffDrive plugin -> simulated robot
```

Camera perception uses:

```text
Gazebo camera -> /camera/image_raw -> perception node -> detection/debug topics
```

Ball control uses:

```text
/camera/image_raw
  -> footbot_perception ball_detector
  -> /ball_detection
  -> footbot_soccer_behavior ball_state_estimator
  -> /soccer/ball_state
  -> footbot_soccer_behavior ball_control_fsm
  -> /cmd_vel
```

## Control Ownership

Only one active node or bridge should publish meaningful commands to `/cmd_vel`
at a time.

| Mode | `/cmd_vel` owner |
| --- | --- |
| Base/manual simulation | human ROS topic commands or HTTP bridge |
| Gesture control | `gesture_to_cmd_vel` |
| Simple ball follower | `ball_follower` |
| Ball control | `ball_control_fsm` |
| Opponent/goal detection | none |
| Soccer field visualization | none |

## Shared Code

`footbot_common` owns shared constants for topics, frames, dimensions, and small
math helpers. It must stay lightweight and reusable. Behavior-specific logic
belongs in `footbot_soccer_behavior`, not in common code.

## Planned Architecture Direction

Use FSM or hierarchical FSM orchestration for high-level behavior, skills for
bounded motion primitives, deterministic control where practical, and optional
future policy modules for tactical experiments.
