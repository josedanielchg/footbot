# Worlds And Scenarios

Gazebo worlds live in:

```text
simulation/ros2_ws/src/footbot_gazebo/worlds/
```

Important worlds:

| World | Purpose |
| --- | --- |
| `footbot_empty.sdf` | Minimal world. |
| `footbot_camera_test.sdf` | Colored objects for camera validation. |
| `footbot_ball_follow.sdf` | Simple ball-follower test scene. |
| `footbot_ball_control.sdf` | One robot plus dynamic ball scenarios. |
| `footbot_ball_control_multi.sdf` | Three isolated ball-control lanes. |
| `footbot_opponent_detection.sdf` | Opponent-detection placeholders. |
| `footbot_soccer_field.sdf` | Field, walls, goals, center ball, and mirrored teams. |

Validate worlds:

```bash
ign sdf -k simulation/ros2_ws/src/footbot_gazebo/worlds/footbot_ball_control.sdf
ign sdf -k simulation/ros2_ws/src/footbot_gazebo/worlds/footbot_soccer_field.sdf
```

## Dynamic Ball

The orange ball model lives under:

```text
simulation/ros2_ws/src/footbot_gazebo/models/orange_ball/
```

It uses friction, reduced bounce, velocity decay, and the custom
`footbot_ball_drag_system` plugin so the ball does not roll forever after
contact.

## Robot Model

The robot model is generated from:

```text
simulation/ros2_ws/src/footbot_description/urdf/footbot.urdf.xacro
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
