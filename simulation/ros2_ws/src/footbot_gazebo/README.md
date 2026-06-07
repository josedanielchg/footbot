# footbot_gazebo

Gazebo worlds, models, bridge reference config, and simulation plugins.

## Contents

- Worlds for camera tests, ball following, ball control, opponent detection, and soccer-field visualization.
- `models/orange_ball` for the dynamic orange ball.
- `src/BallDragSystem.cc`, a Gazebo system plugin that adds predictable ball rolling resistance.
- `config/ros_gz_bridge.yaml`, a reference bridge mapping file.

## Important Worlds

```text
footbot_empty.sdf
footbot_camera_test.sdf
footbot_ball_follow.sdf
footbot_ball_control.sdf
footbot_ball_control_multi.sdf
footbot_reach_goal.sdf
footbot_opponent_detection.sdf
footbot_soccer_field.sdf
```

Validate a world:

```bash
ign sdf -k simulation/ros2_ws/src/footbot_gazebo/worlds/footbot_soccer_field.sdf
```

See `simulation/docs/en/worlds-and-scenarios.md` for the world catalog and plugin notes.
